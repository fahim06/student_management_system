import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from student_management_app.models import Subject, Student, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudent


def student_home(request):
    students = Student.objects.all()
    return render(request, "student_template/student_home_template.html", {"students": students})


def student_view_attendance(request):
    student = Student.objects.get(admin=request.user.id)
    course = student.course_id
    subjects = Subject.objects.filter(course_id=course)
    return render(request, "student_template/student_view_attendance_template.html", {"subjects": subjects})


def student_view_attendance_post(request):
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
    return render(request, "student_template/student_attendance_data_template.html",
                  {"attendance_reports": attendance_reports})


def student_apply_leave(request):
    student_obj = Student.objects.get(admin=request.user.id)
    leave_data = LeaveReportStudent.objects.filter(student_id=student_obj)
    return render(request, "student_template/student_apply_leave_template.html", {"leave_data": leave_data})


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
    student_id = Student.objects.get(admin=request.user.id)
    feedback_data = FeedBackStudent.objects.filter(student_id=student_id)
    return render(request, "student_template/student_feedback_template.html", {"feedback_data": feedback_data})


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
