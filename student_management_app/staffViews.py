import json

from django.contrib import messages
from django.core import serializers
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from student_management_app.models import Subject, SessionYear, Student, Attendance, AttendanceReport, Staff, \
    LeaveReportStaff, FeedBackStaff, CustomUser


def staff_home(request):
    """
    This view gathers all the necessary statistics for the staff dashboard.
    """
    # --- Core Data Fetching ---
    # Get the staff object and all subjects they teach
    staff_user = Staff.objects.get(admin=request.user)
    subjects = Subject.objects.filter(staff_id=request.user)

    # --- Dashboard Card Statistics ---
    subject_count = subjects.count()
    attendance_count = Attendance.objects.filter(subject_id__in=subjects).count()
    leave_count = LeaveReportStaff.objects.filter(staff_id=staff_user, leave_status=1).count()

    # Get unique students taught by this staff
    course_ids = subjects.values_list('course_id', flat=True).distinct()
    student_count = Student.objects.filter(course_id__in=course_ids).count()

    # --- "Attend Subject" Bar Chart Data ---
    # Get attendance count per subject in a single query
    subject_attendance = subjects.annotate(attendance_count=Count('attendance')).values_list('subject_name',
                                                                                             'attendance_count')
    subject_names = [item[0] for item in subject_attendance]
    subject_attendance_counts = [item[1] for item in subject_attendance]

    # --- "Student attendance data" Bar Chart Data ---
    # Get all students in the courses taught by the staff
    students_in_courses = Student.objects.filter(course_id__in=course_ids).select_related('admin').order_by(
        'admin__first_name')

    # Get present/absent counts for each student in a single query
    student_attendance_data = students_in_courses.annotate(
        present_count=Count('attendancereport', filter=Q(attendancereport__status=True)),
        absent_count=Count('attendancereport', filter=Q(attendancereport__status=False))
    ).values('admin__username', 'present_count', 'absent_count')

    student_names_list = [item['admin__username'] for item in student_attendance_data]
    present_counts_list = [item['present_count'] for item in student_attendance_data]
    absent_counts_list = [item['absent_count'] for item in student_attendance_data]

    # --- Prepare Context for Template ---
    context = {
        # Card stats
        "student_count": student_count,
        "attendance_count": attendance_count,
        "leave_count": leave_count,
        "subject_count": subject_count,
        # "Attend Subject" chart
        "data1": subject_attendance_counts,
        "data_name": subject_names,
        # "Student attendance data" chart
        "student_list": student_names_list,
        "present_list": present_counts_list,
        "absent_list": absent_counts_list,
    }
    return render(request, "staff_template/staff_home_template.html", context)


def staff_take_attendance(request):
    subjects = Subject.objects.filter(staff_id=request.user)
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


def staff_update_attendance(request):
    subjects = Subject.objects.filter(staff_id=request.user)
    session_year_id = SessionYear.objects.all()
    return render(request, "staff_template/staff_update_attendance_template.html",
                  {"subjects": subjects, "session_year_id": session_year_id})


@csrf_exempt
def get_attendance_dates(request):
    subject = request.POST.get("subject")
    session_year_id = request.POST.get("session_year_id")
    subject_obj = Subject.objects.get(id=subject)
    session_year_obj = SessionYear.objects.get(id=session_year_id)
    attendance = Attendance.objects.filter(subject_id=subject_obj, session_year_id=session_year_obj)
    attendance_obj = []
    for attendance_single in attendance:
        data = {"id": attendance_single.id, "attendance_date": str(attendance_single.attendance_date),
                "session_year_id": attendance_single.session_year_id.id}
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj), safe=False)


@csrf_exempt
def get_student_attendance(request):
    attendance_date = request.POST.get("attendance_date")
    attendance = Attendance.objects.get(id=attendance_date)

    attendance_date = AttendanceReport.objects.filter(attendance_id=attendance)
    list_data = []

    for student in attendance_date:
        data_small = {"id": student.student_id.admin.id,
                      "name": student.student_id.admin.first_name + " " + student.student_id.admin.last_name,
                      "status": student.status}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def save_update_attendance_data(request):
    student_ids = request.POST.get("student_ids")
    attendance_date = request.POST.get("attendance_date")
    attendance = Attendance.objects.get(id=attendance_date)

    json_student = json.loads(student_ids)

    try:
        for stud in json_student:
            student = Student.objects.get(admin=stud['id'])
            attendance_report = AttendanceReport.objects.get(student_id=student, attendance_id=attendance)
            attendance_report.status = stud['status']
            attendance_report.save()
        return HttpResponse("OK")

    except:
        return HttpResponse("Error")


def staff_apply_leave(request):
    staff_obj = Staff.objects.get(admin=request.user)
    leave_data = LeaveReportStaff.objects.filter(staff_id=staff_obj)
    return render(request, "staff_template/staff_apply_leave_template.html", {"leave_data": leave_data})


def staff_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date = request.POST.get("leave_date")
        leave_message = request.POST.get("leave_message")

        staff_obj = Staff.objects.get(admin=request.user)
        try:
            leave_report = LeaveReportStaff(staff_id=staff_obj, leave_date=leave_date, leave_message=leave_message,
                                            leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except Exception as e:
            messages.error(request, f"Failed to Apply for Leave: {e}")
            return HttpResponseRedirect(reverse("staff_apply_leave"))


def staff_feedback(request):
    staff_id = Staff.objects.get(admin=request.user)
    feedback_data = FeedBackStaff.objects.filter(staff_id=staff_id)
    return render(request, "staff_template/staff_feedback_template.html", {"feedback_data": feedback_data})


def staff_feedback_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_feedback"))
    else:
        feedback_message = request.POST.get("feedback_message")

        staff_obj = Staff.objects.get(admin=request.user.id)
        try:
            feedback = FeedBackStaff(staff_id=staff_obj, feedback=feedback_message, feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        except Exception as e:
            messages.error(request, f"Failed to send feedback: {e}")
            return HttpResponseRedirect(reverse("staff_feedback"))


def staff_add_result(request):
    pass


def staff_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staff.objects.get(admin=user)
    return render(request, "staff_template/staff_profile_template.html", {"user": user, "staff": staff})


def staff_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        address = request.POST.get("address")
        password = request.POST.get("password")

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()

            staff = Staff.objects.get(admin=request.user)
            staff.address = address
            staff.save()
            messages.success(request, "Successfully Edited Profile")
            return HttpResponseRedirect(reverse("staff_profile"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Profile: {e}")
        return HttpResponseRedirect(reverse("staff_profile"))
