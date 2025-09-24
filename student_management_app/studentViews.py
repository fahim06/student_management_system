import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from student_management_app.models import Subject, Student, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudent, Courses


def student_home(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)

    student_obj = Student.objects.get(admin=request.user.id)
    attendance_total = AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student_id=student_obj, status=False).count()
    course = Courses.objects.get(id=student_obj.course_id.id)
    subjects = Subject.objects.filter(course_id=course).count()

    subject_name = []
    data_present = []
    data_absent = []
    subject_data = Subject.objects.filter(course_id=student_obj.course_id)
    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=True).count()
        attendance_absent_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=False).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    context = {"total_attendance": attendance_total, "absent_attendance": attendance_absent,
               "present_attendance": attendance_present, "subjects": subjects, "data1": data_present,
               "data2": data_absent, "data_name": subject_name, "student": student}
    return render(request, "student_template/student_home_template.html", context)


def student_view_attendance(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)
    student_obj = Student.objects.get(admin=request.user.id)
    course = student_obj.course_id
    subjects = Subject.objects.filter(course_id=course)
    context = {"subjects": subjects, "student": student}
    return render(request, "student_template/student_view_attendance_template.html", context)


def student_view_attendance_post(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)
    subject_id = request.POST.get('subject')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    start_date_parse = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_parse = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    subject_obj = Subject.objects.get(id=subject_id)
    user_obj = CustomUser.objects.get(id=request.user.id)
    student_obj = Student.objects.get(admin=user_obj)
    attendance = Attendance.objects.filter(attendance_date__range=(start_date_parse, end_date_parse),
                                           subject_id=subject_obj)
    attendance_reports = AttendanceReport.objects.filter(attendance_id__in=attendance, student_id=student_obj)
    context = {"attendance_reports": attendance_reports, "student": student}
    return render(request, "student_template/student_attendance_data_template.html", context)


def student_apply_leave(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)
    student_obj = Student.objects.get(admin=request.user.id)
    leave_data = LeaveReportStudent.objects.filter(student_id=student_obj)
    context = {"leave_data": leave_data, "student": student}
    return render(request, "student_template/student_apply_leave_template.html", context)


def student_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date = request.POST.get("leave_date")
        leave_message = request.POST.get("leave_message")

        student_obj = Student.objects.get(admin=request.user.id)
        try:
            leave_report = LeaveReportStudent(student_id=student_obj, leave_date=leave_date,
                                              leave_message=leave_message,
                                              leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except Exception as e:
            messages.error(request, f"Failed to Apply for Leave: {e}")
            return HttpResponseRedirect(reverse("student_apply_leave"))


def student_feedback(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)
    student_id = Student.objects.get(admin=request.user.id)
    feedback_data = FeedBackStudent.objects.filter(student_id=student_id)
    context = {"feedback_data": feedback_data, "student": student}
    return render(request, "student_template/student_feedback_template.html", context)


def student_feedback_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_feedback_save"))
    else:
        feedback_message = request.POST.get("feedback_message")

        student_obj = Student.objects.get(admin=request.user.id)
        try:
            feedback = FeedBackStudent(student_id=student_obj, feedback=feedback_message, feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))
        except Exception as e:
            messages.error(request, f"Failed to send feedback: {e}")
            return HttpResponseRedirect(reverse("student_feedback"))


def student_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Student.objects.get(admin=user)
    context = {"user": user, "student": student}
    return render(request, "student_template/student_profile_template.html", context)


def student_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_profile"))
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

            student = Student.objects.get(admin=customuser)
            student.address = address
            student.save()
            messages.success(request, "Successfully Edited Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Profile: {e}")
        return HttpResponseRedirect(reverse("student_profile"))
