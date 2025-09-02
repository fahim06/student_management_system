import json

from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from student_management_app.models import Subject, SessionYear, Student, Attendance, AttendanceReport


def staff_home(request):
    return render(request, "staff_template/staff_home_template.html")


def staff_take_attendance(request):
    subjects = Subject.objects.filter(staff_id=request.user.id)
    session_years = SessionYear.objects.all()
    return render(request, "staff_template/staff_take_attendance_template.html",
                  {"subjects": subjects, "session_years": session_years})


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_year = request.POST.get('session_year')

    subject = Subject.objects.get(id=subject_id)
    session_model = SessionYear.objects.get(id=session_year)
    students = Student.objects.filter(course_id=subject.course_id, session_year_id=session_model)
    student_data = serializers.serialize("python", students)
    list_data = []

    for student in students:
        data_small = {"id": student.admin.id, "name": student.admin.first_name + " " + student.admin.last_name}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def save_attendance_data(request):
    student_ids = request.POST.get("student_ids")
    subject_id = request.POST.get("subject_id")
    attendance_date = request.POST.get("attendance_date")
    session_year_id = request.POST.get("session_year_id")

    subject_model = Subject.objects.get(id=subject_id)
    session_model = SessionYear.objects.get(id=session_year_id)
    json_student = json.loads(student_ids)

    try:
        attendance = Attendance(subject_id=subject_model, attendance_date=attendance_date,
                                session_year_id=session_model)
        attendance.save()

        for stud in json_student:
            student = Student.objects.get(admin=stud['id'])
            attendance_report = AttendanceReport(student_id=student, attendance_id=attendance, status=stud['status'])
            attendance_report.save()
        return HttpResponse("OK")

    except:
        return HttpResponse("Error")
