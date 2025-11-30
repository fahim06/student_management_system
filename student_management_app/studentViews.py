import datetime

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from student_management_app.models import Subject, Student, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudent, NotificationStudent, StudentResult


def student_home(request):
    # Use select_related to efficiently fetch related user, course, and session data in a single query.
    student = Student.objects.select_related('admin', 'course', 'session_year').get(admin=request.user)

    # Use annotations for more efficient counting.
    attendance_stats = AttendanceReport.objects.filter(student_id=student).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status=True)),
        absent=Count('id', filter=Q(status=False))
    )

    subjects_count = Subject.objects.filter(course=student.course).count()

    # Initialize data for charts and subject counts
    subject_name = []
    data_present = []
    data_absent = []
    subject_data = Subject.objects.filter(course=student.course)
    for subject in subject_data:
        # This loop can cause N+1 query issues. Consider optimizing if performance is critical.
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=True).count()
        attendance_absent_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=False).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    context = {
        "total_attendance": attendance_stats.get('total', 0),
        "absent_attendance": attendance_stats.get('absent', 0),
        "present_attendance": attendance_stats.get('present', 0),
        "subjects": subjects_count,
        "data1": data_present,
        "data2": data_absent,
        "data_name": subject_name, "student": student}
    return render(request, "student_template/student_home_template.html", context)


def student_view_attendance(request):
    """
    Handles both displaying the attendance filter form (GET) and showing
    the attendance results based on the filter (POST).
    """
    try:
        student = Student.objects.select_related('course').get(admin=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Could not find student profile.")
        return HttpResponseRedirect(reverse('student_home'))

    subjects = Subject.objects.filter(course=student.course)
    context = {
        "subjects": subjects,
        "student": student
    }

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        # Add selected values to context to repopulate the form
        context.update({
            'selected_subject_id': subject_id,
            'start_date': start_date_str,
            'end_date': end_date_str,
        })

        try:
            # Validate and parse dates
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

            # A more efficient, single query to get the reports
            attendance_reports = AttendanceReport.objects.filter(
                student=student,
                attendance__subject_id=subject_id,
                attendance__attendance_date__range=(start_date, end_date)
            ).select_related('attendance', 'attendance__subject')

            context['attendance_reports'] = attendance_reports

        except (ValueError, TypeError):
            messages.error(request, "Invalid date format. Please select a valid start and end date.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return render(request, "student_template/student_view_attendance_template.html", context)


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
        profile_pic = request.FILES.get("profile_pic")

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            if password is not None and password != "":
                customuser.set_password(password)
            customuser.save()

            student = Student.objects.get(admin=customuser)
            student.address = address
            if profile_pic:
                student.profile_picture = profile_pic
            student.save()

            messages.success(request, "Successfully Edited Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Profile: {e}")
            return HttpResponseRedirect(reverse("student_profile"))


@csrf_exempt
def student_fcmtoken_save(request):
    token = request.POST.get("token")

    try:
        student = Student.objects.get(admin=request.user.id)
        student.fcm_token = token
        student.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("Error")


def student_all_notifications(request):
    student = Student.objects.get(admin=request.user.id)
    notifications = NotificationStudent.objects.filter(student_id=student.id)
    context = {"notifications": notifications, "student": student}
    return render(request, "student_template/student_all_notifications_template.html", context)


def student_view_result(request):
    student = Student.objects.get(admin=request.user)
    results = StudentResult.objects.filter(student=student).select_related('subject')

    for result in results:
        max_exam_marks = 75
        max_assignment_marks = 25
        total_possible = max_exam_marks + max_assignment_marks
        result.total_marks = result.subject_exam_marks + result.subject_assignment_marks
        try:
            result.percentage = (result.total_marks / total_possible) * 100
        except ZeroDivisionError:
            result.percentage = 0

        # Calculate Grade based on the percentage
        if result.percentage >= 80:
            result.grade_point = 4.0
            result.grade = "A+"
        elif result.percentage >= 75:
            result.grade_point = 3.75
            result.grade = "A"
        elif result.percentage >= 70:
            result.grade_point = 3.50
            result.grade = "A-"
        elif result.percentage >= 65:
            result.grade_point = 3.25
            result.grade = "B+"
        elif result.percentage >= 60:
            result.grade_point = 3.0
            result.grade = "B"
        elif result.percentage >= 55:
            result.grade_point = 2.75
            result.grade = "B-"
        elif result.percentage >= 50:
            result.grade_point = 2.50
            result.grade = "C+"
        elif result.percentage >= 45:
            result.grade_point = 2.25
            result.grade = "C"
        elif result.percentage >= 40:
            result.grade_point = 2.0
            result.grade = "D"
        else:
            result.grade = "F"

        # Calculate Grade Point (GPA) based on the grade
        # if result.grade.startswith("A"):
        #     result.grade_point = 4.0
        # elif result.grade.startswith("B"):
        #     result.grade_point = 3.0
        # elif result.grade.startswith("C"):
        #     result.grade_point = 2.0
        # elif result.grade == "D":
        #     result.grade_point = 1.0
        # else:
        #     result.grade_point = 0.0

        result.status = "Pass" if result.subject_exam_marks >= 30 else "Fail"

    context = {
        'results': results,
        'student': student,  # Pass student for the base template
    }

    return render(request, "student_template/student_view_result_template.html", context)
