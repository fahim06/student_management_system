import json
import os

from django.contrib import messages
from django.contrib.sites import requests
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from student_management_app.forms import AddStudentForm, EditStudentForm
from student_management_app.models import CustomUser, Courses, Staff, Subject, Student, SessionYear, FeedBackStudent, \
    FeedBackStaff, LeaveReportStudent, LeaveReportStaff, Attendance, AttendanceReport, NotificationStudent, \
    NotificationStaff


def admin_home(request):
    """
    View for the main admin dashboard. Gathers all necessary data for the
    summary cards and charts.
    """
    # --- 1. Summary Card Statistics ---
    # Simple counts for the info boxes at the top of the page.

    student_count = Student.objects.all().count()
    staff_count = Staff.objects.all().count()
    subject_count = Subject.objects.all().count()
    course_count = Courses.objects.all().count()

    # --- 2. Data for Course-related Charts ---
    course_data = Courses.objects.annotate(
        subject_count=Count('subject'),
        student_count=Count('student')
    ).values('course_name', 'subject_count', 'student_count')

    course_name_list = [item['course_name'] for item in course_data]
    subject_cont_list = [item['subject_count'] for item in course_data]
    student_count_list_in_course = [item['student_count'] for item in course_data]

    # --- 3. Data for Subject-related Chart ---
    subject_data = Subject.objects.select_related('course').annotate(
        student_count_in_course=Count('course__student')
    ).values('subject_name', 'student_count_in_course')

    subject_list_for_pie_chart = [item['subject_name'] for item in subject_data]
    student_count_in_subject_for_pie_chart = [item['student_count_in_course'] for item in subject_data]

    # --- 4. Data for Staff Attendance Chart ---
    staff_attendance_data = Staff.objects.select_related('admin').annotate(
        attendance_count=Count('subject__attendance'),
        leave_count=Count('leavereportstaff', filter=Q(leavereportstaff__leave_status=1))
    ).values('admin__username', 'attendance_count', 'leave_count')

    staff_name_list = [item['admin__username'] for item in staff_attendance_data]
    attendance_present_list_staff = [item['attendance_count'] for item in staff_attendance_data]
    attendance_absent_list_staff = [item['leave_count'] for item in staff_attendance_data]

    # --- 5. Data for Student Attendance Chart ---
    student_attendance_data = Student.objects.select_related('admin').annotate(
        present_count=Count('attendancereport', filter=Q(attendancereport__status=True)),
        absent_count=Count('attendancereport', filter=Q(attendancereport__status=False)),
        leave_count=Count('leavereportstudent', filter=Q(leavereportstudent__leave_status=1))
    ).values('admin__username', 'present_count', 'absent_count', 'leave_count')

    student_name_list = [item['admin__username'] for item in student_attendance_data]
    attendance_present_list_student = [item['present_count'] for item in student_attendance_data]
    # Total "absences" is a sum of unapproved attendance and approved leaves.
    attendance_absent_list_student = [item['absent_count'] + item['leave_count'] for item in student_attendance_data]

    # --- 6. Prepare Context and Render Template ---
    context = {
        # Summary Card Data
        "student_count": student_count,
        "staff_count": staff_count,
        "subject_count": subject_count,
        "course_count": course_count,

        # --- Data for "Total subject in each course" (Chart 2) ---
        "course_name_list": course_name_list,
        "subject_cont_list": subject_cont_list,

        # --- Data for "Total student in each course" (Chart 3) ---
        "student_count_list_in_course": student_count_list_in_course,

        # --- Data for "Total Student in Each Subject" (Chart 4) ---
        "subject_list_for_pie_chart": subject_list_for_pie_chart,
        "student_count_in_subject_for_pie_chart": student_count_in_subject_for_pie_chart,

        # --- Data for "Staff Attendance vs. Leave" (Chart 5) ---
        "staff_name_list": staff_name_list,
        "attendance_present_list_staff": attendance_present_list_staff,
        "attendance_absent_list_staff": attendance_absent_list_staff,

        # --- Data for "Student Attendance vs. Leave" (Chart 6) ---
        "student_name_list": student_name_list,
        "attendance_present_list_student": attendance_present_list_student,
        "attendance_absent_list_student": attendance_absent_list_student,
    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        address = request.POST.get("address")
        profile_pic = request.FILES.get("profile_pic")
        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                  first_name=first_name, last_name=last_name, user_type='2')
            # The user's Staff profile is created by a signal.
            # We need to fetch that profile, update it, and then save it.
            staff_profile = user.staff
            staff_profile.address = address
            if profile_pic:
                staff_profile.profile_pic = profile_pic
            staff_profile.save()
            messages.success(request, "Successfully Added Staff")
            return HttpResponseRedirect(reverse("manage_staff"))
        except Exception as e:
            messages.error(request, f"Failed to Add Staff: {e}")
            return HttpResponseRedirect(reverse("manage_staff"))


def add_course_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        course = request.POST.get("course")
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Successfully Added Course")
            return HttpResponseRedirect(reverse("manage_course"))
        except Exception as e:
            messages.error(request, f"Failed to Add Course: {e}")
            return HttpResponseRedirect(reverse("manage_course"))


def add_student_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        form = AddStudentForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            address = form.cleaned_data["address"]
            session_year_id = form.cleaned_data["session_year_id"]
            course_id = form.cleaned_data["course"]
            sex = form.cleaned_data["sex"]

            # Get the uploaded file object from the validated form data
            profile_picture_file = form.cleaned_data.get("profile_picture")

            try:
                user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                      first_name=first_name, last_name=last_name, user_type='3')
                user.student.address = address
                user.student.course = course_id
                user.student.session_year = session_year_id
                user.student.gender = sex
                if profile_picture_file:
                    user.student.profile_picture = profile_picture_file
                user.save()
                messages.success(request, "Successfully Added Student")
                return HttpResponseRedirect(reverse("manage_student"))
            except Exception as e:
                messages.error(request, f"Failed to Add Student: {e}")
                return HttpResponseRedirect(reverse("manage_student"))
        else:
            messages.error(request, "Please correct the errors below")
            # Re-render the manage_student page with the form containing errors
            return render(request, "hod_template/manage_student_template.html", {"form": form})


def add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_code = request.POST.get("subject_code")
        subject_name = request.POST.get("subject_name")
        course_id = request.POST.get("course")
        course = Courses.objects.get(id=course_id)
        staff_id = request.POST.get("staff")
        staff = Staff.objects.get(admin=staff_id)

        try:
            subject = Subject(subject_code=subject_code, subject_name=subject_name, course=course, staff=staff)
            subject.save()
            messages.success(request, "Successfully Added Subject")
            return HttpResponseRedirect(reverse("manage_subject"))
        except Exception as e:
            messages.error(request, f"Failed to Add Subject: {e}")
            return HttpResponseRedirect(reverse("manage_subject"))


def manage_staff(request):
    staffs = Staff.objects.all()
    return render(request, "hod_template/manage_staff_template.html", {"staffs": staffs})


def manage_student(request):
    students = Student.objects.select_related('admin', 'course', 'session_year').all()
    form = AddStudentForm()
    return render(request, "hod_template/manage_student_template.html",
                  {"students": students, "form": form})


def manage_course(request):
    courses = Courses.objects.all()
    return render(request, "hod_template/manage_course_template.html", {"courses": courses})


def manage_subject(request):
    # Use select_related to pre-fetch related Course and Staff (CustomUser) objects.
    # This is much more efficient than fetching them one by one in the template.
    # Also fetching courses and staffs for the "Add Subject" form dropdowns.
    subjects = Subject.objects.select_related('course', 'staff__admin').all()
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/manage_subject_template.html",
                  {"subjects": subjects, "courses": courses, "staffs": staffs})


def edit_staff(request, staff_id):  # No changes here, just for context
    staff = Staff.objects.get(admin=staff_id)
    return render(request, "hod_template/edit_staff_template.html", {"staff": staff, "id": staff_id})


def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id = request.POST.get("staff_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        address = request.POST.get("address")
        profile_pic = request.FILES.get("profile_pic")

        try:
            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()

            staff_model = Staff.objects.get(admin=staff_id)
            staff_model.address = address
            if profile_pic:
                staff_model.profile_pic = profile_pic
            staff_model.save()

            messages.success(request, "Successfully Edited Staff")
            return HttpResponseRedirect(reverse("manage_staff"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Staff: {e}")
            return HttpResponseRedirect(reverse("manage_staff"))


def edit_student(request, student_id):
    request.session['student_id'] = student_id
    student = Student.objects.get(admin=student_id)
    form = EditStudentForm()
    form.fields['email'].initial = student.admin.email
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    form.fields['username'].initial = student.admin.username
    form.fields['address'].initial = student.address
    form.fields['course'].initial = student.course.id
    form.fields['sex'].initial = student.gender
    form.fields['session_year_id'].initial = student.session_year.id
    return render(request, "hod_template/edit_student_template.html",
                  {"form": form, "id": student_id, "username": student.admin.username})


def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        student_id = request.session.get("student_id")
        if student_id == None:
            return HttpResponseRedirect(reverse("manage_student"))

        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            address = form.cleaned_data["address"]
            session_year_id = form.cleaned_data["session_year_id"]
            course_id = form.cleaned_data["course"]
            sex = form.cleaned_data["sex"]

            # Get the user and student objects
            user = CustomUser.objects.get(id=student_id)
            student = Student.objects.get(admin=student_id)

            # Update CustomUser fields
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.save()

            # Update Student fields
            student.address = address
            student.session_year = session_year_id
            student.gender = sex
            student.course = course_id

            # Correctly handle the profile picture update from the form's cleaned data
            if form.cleaned_data.get('profile_picture'):
                student.profile_picture = form.cleaned_data['profile_picture']

            student.save()
            del request.session['student_id']

            messages.success(request, "Successfully Edited Student")
            return HttpResponseRedirect(reverse("manage_student"))
        else:
            student = Student.objects.get(admin=student_id)
            return render(request, "hod_template/edit_student_template.html",
                          {"form": form, "id": student_id, "username": student.admin.username})


def edit_subject(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/edit_subject_template.html",
                  {"subject": subject, "staffs": staffs, "courses": courses})


def edit_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id = request.POST.get("subject_id")
        subject_code = request.POST.get("subject_code")
        subject_name = request.POST.get("subject_name")
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            subject = Subject.objects.get(id=subject_id)
            subject.subject_code = subject_code
            subject.subject_name = subject_name
            staff = Staff.objects.get(admin=staff_id)
            subject.staff = staff
            course = Courses.objects.get(id=course_id)
            subject.course = course
            subject.save()

            messages.success(request, "Successfully Edited Subject")
            return HttpResponseRedirect(reverse("manage_subject"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Subject: {e}")
            return HttpResponseRedirect(reverse("manage_subject"))


def edit_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    return render(request, "hod_template/edit_course_template.html", {"course": course, "id": course_id, })


def edit_course_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        course_id = request.POST.get("course_id")
        course_name = request.POST.get("course")

        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            course.save()
            messages.success(request, "Successfully Edited Course")
            return HttpResponseRedirect(reverse("manage_course"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Course: {e}")
            return HttpResponseRedirect(reverse("manage_course"))


def manage_session(request):
    sessions = SessionYear.objects.all()
    return render(request, "hod_template/manage_session_template.html", {"sessions": sessions})


def add_session_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        session_start_year = request.POST.get("session_start")
        session_end_year = request.POST.get("session_end")

        try:
            # Create date objects for the first day of the given years
            start_date = f"{session_start_year}-01-01"
            end_date = f"{session_end_year}-01-01"
            session_year = SessionYear(session_start_year=start_date, session_end_year=end_date)
            session_year.save()
            messages.success(request, "Successfully Added Session")
            return HttpResponseRedirect(reverse("manage_session"))
        except Exception as e:
            messages.error(request, f"Failed to Add Session: {e}")
            return HttpResponseRedirect(reverse("manage_session"))


def edit_session(request, session_id):
    session = SessionYear.objects.get(id=session_id)
    # Pass only the year part to the template
    context = {
        "session": session,
        "session_start_year": session.session_start_year.strftime("%Y"),
        "session_end_year": session.session_end_year.strftime("%Y")
    }
    return render(request, "hod_template/edit_session_template.html", context)


def edit_session_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        session_id = request.POST.get("session_id")
        session_start_year = request.POST.get("session_start")
        session_end_year = request.POST.get("session_end")

        try:
            session = SessionYear.objects.get(id=session_id)
            session.session_start_year = f"{session_start_year}-01-01"
            session.session_end_year = f"{session_end_year}-01-01"
            session.save()
            messages.success(request, "Successfully Edited Session")
            return HttpResponseRedirect(reverse("manage_session"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Session: {e}")
            return HttpResponseRedirect(reverse("manage_session"))


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_id = request.POST.get("user_id")  # Get user_id if it exists
    query = CustomUser.objects.filter(email=email)
    if user_id:
        query = query.exclude(id=user_id)  # Exclude the current user when checking
    user_obj = query.exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_id = request.POST.get("user_id")  # Get user_id if it exists
    query = CustomUser.objects.filter(username=username)
    if user_id:
        query = query.exclude(id=user_id)  # Exclude the current user when checking
    user_obj = query.exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def staff_feedback_message(request):
    feedbacks = FeedBackStaff.objects.all()
    return render(request, "hod_template/staff_feedback_template.html", {"feedbacks": feedbacks})


@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackStaff.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


def student_feedback_message(request):
    feedbacks = FeedBackStudent.objects.all()
    return render(request, "hod_template/student_feedback_template.html", {"feedbacks": feedbacks})


@csrf_exempt
def student_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackStudent.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


def staff_leave_view(request):
    leaves = LeaveReportStaff.objects.all()
    return render(request, "hod_template/staff_leave_view_template.html", {"leaves": leaves})


def student_leave_view(request):
    leaves = LeaveReportStudent.objects.all()
    return render(request, "hod_template/student_leave_view_template.html", {"leaves": leaves})


def student_approve_leave(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))


def student_disapprove_leave(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))


def staff_approve_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def staff_disapprove_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def admin_view_attendance(request):
    """
    Renders the initial page for viewing attendance.
    This view provides the necessary data for the filter dropdowns.
    """
    subjects = Subject.objects.all()
    session_years = SessionYear.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "hod_template/admin_view_attendance_template.html", context)


def admin_get_attendance_dates(request):
    """
    Fetches attendance dates for a given subject and session via AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        subject_id = request.POST.get("subject")
        session_year_id = request.POST.get("session_year_id")

        subject_obj = Subject.objects.get(id=subject_id)
        session_year_obj = SessionYear.objects.get(id=session_year_id)

        # Correctly filter using model objects
        attendances = Attendance.objects.filter(subject=subject_obj, session_year=session_year_obj)

        # Prepare data for JSON response
        attendance_list = []
        for attendance in attendances:
            data = {
                "id": attendance.id,
                "attendance_date": str(attendance.attendance_date),
                # Correctly access the integer ID
                "session_year_id": attendance.session_year_id
            }
            attendance_list.append(data)

        return JsonResponse(attendance_list, safe=False)

    except (Subject.DoesNotExist, SessionYear.DoesNotExist):
        return JsonResponse({"error": "Invalid subject or session"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def admin_get_student_attendance(request):
    """
    Fetches all student attendance records for a specific attendance date via AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        attendance_id = request.POST.get("attendance_date")
        attendance = Attendance.objects.get(id=attendance_id)

        # Use select_related for an efficient query
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance).select_related('student__admin')

        student_data = []
        for report in attendance_reports:
            data = {
                # Correctly access attributes from the related objects
                "id": report.student.admin.id,
                "name": f"{report.student.admin.first_name} {report.student.admin.last_name}",
                "status": report.status
            }
            student_data.append(data)

        return JsonResponse(student_data, safe=False)

    except Attendance.DoesNotExist:
        return JsonResponse({"error": "Attendance record not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def admin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "hod_template/admin_profile_template.html", {"user": user})


def admin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        profile_pic_file = request.FILES.get('profile_pic')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            admin_profile = customuser.adminhod
            if profile_pic_file:
                admin_profile.profile_pic = profile_pic_file
            admin_profile.save()

            if password is not None and password != "":
                customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Edited Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Profile: {e}")
            return HttpResponseRedirect(reverse("admin_profile"))


def admin_send_notification_student(request):
    students = Student.objects.all()
    return render(request, "hod_template/student_notification_template.html", {"students": students})


def admin_send_notification_staff(request):
    staffs = Staff.objects.all()
    return render(request, "hod_template/staff_notification_template.html", {"staffs": staffs})


@csrf_exempt
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = Student.objects.get(admin=id)
    token = student.fcm_token
    url = "https://fcm.googleapis.com/fcm/send"
    body = {
        "to": token,
        "notification": {
            "title": "Student management system",
            "body": message
        }

    }
    headers = {"Content-Type": "application/json", "Authorization": "key=" + os.getenv('FCM_KEY')}
    data = requests.post(url, data=json.dumps(body), headers=headers)
    notification = NotificationStudent(student_id=student, message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")


@csrf_exempt
def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = Staff.objects.get(admin=id)
    token = staff.fcm_token
    url = "https://fcm.googleapis.com/fcm/send"
    body = {
        "to": token,
        "notification": {
            "title": "Student management system",
            "body": message
        }

    }
    headers = {"Content-Type": "application/json", "Authorization": "key=" + os.getenv('FCM_KEY')}
    data = requests.post(url, data=json.dumps(body), headers=headers)
    notification = NotificationStaff(staff_id=staff, message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")
