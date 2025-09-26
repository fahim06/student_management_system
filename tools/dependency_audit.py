#!/usr/bin/env python3
"""
Dependency audit script for Python projects using requirements.txt.
- Audits dependencies via OSV.dev for known vulnerabilities.
- Checks available versions via PyPI to suggest patch/minor updates and flag major updates to batch.
- Outputs a Markdown file at repo root: dependency-audit-<YYYY-MM-DD>.md

This script avoids external dependencies (uses urllib); if the 'packaging' module is available, it will use it for version comparisons.
"""
import datetime
import json
import os
import re
import sys
from typing import List, Optional, Tuple

try:
    from packaging.version import Version, InvalidVersion
    from packaging.specifiers import SpecifierSet

    HAVE_PACKAGING = True
except Exception:  # packaging might not be installed
    HAVE_PACKAGING = False

import urllib.request
import urllib.error

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
REQ_FILE = os.path.join(REPO_ROOT, 'requirements.txt')

PYPI_JSON_URL = 'https://pypi.org/pypi/{name}/json'
OSV_QUERY_URL = 'https://api.osv.dev/v1/query'


def http_get(url: str, timeout: int = 20) -> Optional[bytes]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'dependency-audit-script/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        return None


def http_post_json(url: str, payload: dict, timeout: int = 30) -> Optional[dict]:
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json',
                                                              'User-Agent': 'dependency-audit-script/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None


class SimpleVersion:
    """Fallback version comparator if 'packaging' is unavailable. Very naive.
    Only handles numeric dot-separated versions and compares lexicographically per segment.
    """

    def __init__(self, s: str):
        self.original = s
        self.parts = self._parse(s)

    @staticmethod
    def _parse(s: str) -> Tuple[int, ...]:
        nums = []
        for part in re.split(r'[^0-9]+', s):
            if part == '':
                continue
            try:
                nums.append(int(part))
            except ValueError:
                nums.append(0)
        return tuple(nums)

    def __lt__(self, other: 'SimpleVersion'):
        return self.parts < other.parts

    def __eq__(self, other: 'SimpleVersion'):
        return self.parts == other.parts


DefVersion = Version if HAVE_PACKAGING else SimpleVersion


def normalize_name(name: str) -> str:
    return re.sub(r'[-_]+', '-', name).lower().strip()


def parse_requirements(path: str) -> List[Tuple[str, str]]:
    """
    Returns list of (name, spec) where spec is the raw spec string (could be empty for unconstrained)
    """
    deps = []
    if not os.path.exists(path):
        return deps
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # remove inline comments
            if ' #' in line:
                line = line.split(' #', 1)[0].strip()
            # skip editable and URLs
            if line.startswith('-e ') or '://' in line:
                continue
            # Split name and spec
            m = re.match(r'^([A-Za-z0-9_.\-]+)\s*(.*)$', line)
            if not m:
                continue
            name = m.group(1)
            spec = m.group(2).strip()
            deps.append((name, spec))
    return deps


def get_pypi_info(name: str) -> Optional[dict]:
    data = http_get(PYPI_JSON_URL.format(name=name))
    if not data:
        return None
    try:
        return json.loads(data.decode('utf-8'))
    except Exception:
        return None


def latest_versions(name: str, spec: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (latest_compatible, latest_overall) as version strings.
    If spec is unconstrained, latest_compatible == latest_overall.
    """
    info = get_pypi_info(name)
    if not info:
        return (None, None)
    releases = info.get('releases', {})
    all_versions = sorted([v for v in releases.keys() if releases.get(v)], key=lambda v: DefVersion(v))
    latest_overall = all_versions[-1] if all_versions else None

    if not spec:
        return (latest_overall, latest_overall)

    if HAVE_PACKAGING:
        try:
            ss = SpecifierSet(spec)
            compat = [v for v in all_versions if Version(v) in ss]
            latest_compat = compat[-1] if compat else None
        except Exception:
            latest_compat = None
    else:
        # Very naive handling: support ~=X.Y and ==X.Y.Z and >=, <= basic
        latest_compat = None
        m = re.search(r'~=\s*([0-9]+\.[0-9]+)', spec)
        if m:
            prefix = m.group(1) + '.'
            compat = [v for v in all_versions if v.startswith(prefix)]
            latest_compat = compat[-1] if compat else None
        m2 = re.search(r'==\s*([0-9][^,\s]+)', spec)
        if m2:
            target = m2.group(1)
            latest_compat = target if target in all_versions else None
    return (latest_compat, latest_overall)


def semver_relation(current: Optional[str], latest: Optional[str]) -> Optional[str]:
    if not current or not latest:
        return None
    try:
        cv = DefVersion(current)
        lv = DefVersion(latest)
    except Exception:
        return None

    # Compare major/minor/patch by splitting numeric parts (best-effort)
    def parts(v):
        s = str(v)
        nums = re.split(r'[^0-9]+', s)
        nums = [int(x) for x in nums if x != '']
        while len(nums) < 3:
            nums.append(0)
        return nums[:3]

    cmaj, cmin, cpat = parts(cv)
    lmaj, lmin, lpat = parts(lv)
    if lmaj > cmaj:
        return 'major'
    if lmin > cmin:
        return 'minor'
    if lpat > cpat:
        return 'patch'
    return 'same'


def osv_vulns(name: str, version: Optional[str]) -> List[dict]:
    if not version:
        return []
    payload = {
        "package": {"name": name, "ecosystem": "PyPI"},
        "version": version
    }
    resp = http_post_json(OSV_QUERY_URL, payload)
    vulns = []
    if not resp:
        return vulns
    for v in resp.get('vulns', []) or []:
        # Extract severity if available
        sev = None
        severities = v.get('severity') or []
        if severities:
            # pick the highest score/text if multiple
            sev = ', '.join(sorted({f"{s.get('type', '')}:{s.get('score', '')}" for s in severities}))
        # Fixed versions from ranges
        fixed = set()
        for aff in v.get('affected', []) or []:
            for rng in aff.get('ranges', []) or []:
                for ev in rng.get('events', []) or []:
                    if 'fixed' in ev:
                        fixed.add(ev['fixed'])
        vulns.append({
            'id': v.get('id'),
            'summary': v.get('summary') or v.get('details', '')[:140],
            'severity': sev,
            'fixed_versions': sorted(fixed) if fixed else []
        })
    return vulns


def make_report(deps: List[Tuple[str, str]]) -> str:
    today = datetime.date.today().isoformat()
    lines = []
    lines.append(f"# Dependency Audit Report ({today})")
    lines.append("")
    lines.append("Scope: requirements.txt (PyPI)")
    lines.append("")
    lines.append(
        "Summary of dependencies, known vulnerabilities (from OSV), and available updates. Major updates are listed for batching and may include breaking changes.")
    lines.append("")

    majors = []

    # Table header
    lines.append(
        "| Package | Constraint | Resolved (assumed) | Latest Compatible | Latest Overall | Update Type | Vulnerabilities |")
    lines.append("|---|---|---:|---:|---:|---|---|")

    for raw_name, spec in deps:
        name = normalize_name(raw_name)
        latest_compat, latest_overall = latest_versions(name, spec)
        resolved = latest_compat  # assume pip installs latest compatible
        vulns = osv_vulns(name, resolved)
        update_type = semver_relation(resolved, latest_overall) if resolved and latest_overall else None
        if update_type == 'major':
            majors.append((name, resolved, latest_overall))
        vuln_text = 'None'
        if vulns:
            parts_list = []
            for v in vulns:
                fx = f" (fixed in: {', '.join(v['fixed_versions'])})" if v['fixed_versions'] else ''
                sev = f"; severity: {v['severity']}" if v['severity'] else ''
                parts_list.append(f"{v['id']}{sev}{fx}")
            vuln_text = '; '.join(parts_list)
        lines.append(
            f"| {name} | {spec or '(unconstrained)'} | {resolved or '-'} | {latest_compat or '-'} | {latest_overall or '-'} | {update_type or '-'} | {vuln_text} |"
        )

    lines.append("")
    if majors:
        lines.append("## Major updates to batch (possible breaking changes)")
        lines.append("")
        for name, cur, new in majors:
            lines.append(f"- {name}: {cur} -> {new}. Review release notes for breaking changes before upgrading.")
        lines.append("")

    lines.append("## Notes")
    lines.append("- Resolved versions assume a fresh install today that satisfies the specified constraints.")
    lines.append("- Vulnerabilities are sourced from OSV.dev based on the resolved version.")
    lines.append("- Patch/minor updates are generally safe; major updates may include breaking changes.")
    lines.append("")

    lines.append("## Next steps")
    lines.append("- You can choose to apply patch/minor updates where tests pass. Reply with approval to proceed.")

    return "\n".join(lines)


def main():
    deps = parse_requirements(REQ_FILE)
    if not deps:
        print("No dependencies found in requirements.txt", file=sys.stderr)
        return 1
    report = make_report(deps)
    out_name = f"dependency-audit-{datetime.date.today().isoformat()}.md"
    out_path = os.path.join(REPO_ROOT, out_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Wrote {out_name}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
