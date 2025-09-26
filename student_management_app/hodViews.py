import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from student_management_app.forms import AddStudentForm, EditStudentForm
from student_management_app.models import CustomUser, Courses, Staff, Subject, Student, SessionYear, FeedBackStudent, \
    FeedBackStaff, LeaveReportStudent, LeaveReportStaff, Attendance, AttendanceReport


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

    # --- 2. Data for Charts ---

    # Chart: "Total subject in each course" & "Total student in each course"
    # A single query to get subject and student counts grouped by course.

    course_data = Courses.objects.annotate(
        subject_count=Count('subject'),
        student_count=Count('student')
    ).values('course_name', 'subject_count', 'student_count')

    # Unpack the data for the template context

    course_name_list = [item['course_name'] for item in course_data]
    subject_cont_list = [item['subject_count'] for item in course_data]
    student_count_list_in_course = [item['student_count'] for item in course_data]

    # Chart: "Total Student in Each Subject"
    # This chart shows the number of students in the *course* that a subject belongs to.
    # An efficient query to get this data.

    subject_data = Subject.objects.select_related('course').annotate(
        student_count_in_course=Count('course__student')
    ).values('subject_name', 'student_count_in_course')

    subject_list_for_pie_chart = [item['subject_name'] for item in subject_data]
    student_count_in_subject_for_pie_chart = [item['student_count_in_course'] for item in subject_data]

    # Chart: "Staff Attendance vs. Leave"
    # Efficiently annotates attendance and leave counts directly onto the Staff queryset.

    staff_attendance_data = Staff.objects.select_related('admin').annotate(
        attendance_count=Count('admin__subject__attendance'),
        leave_count=Count('leavereportstaff', filter=Q(leavereportstaff__leave_status=1))
    ).values('admin__username', 'attendance_count', 'leave_count')

    staff_name_list = [item['admin__username'] for item in staff_attendance_data]
    attendance_present_list_staff = [item['attendance_count'] for item in staff_attendance_data]
    attendance_absent_list_staff = [item['leave_count'] for item in staff_attendance_data]

    # Chart: "Student Attendance vs. Leave"
    # Efficiently annotates attendance and leave counts directly onto the Student queryset.

    student_attendance_data = Student.objects.select_related('admin').annotate(
        present_count=Count('attendancereport', filter=Q(attendancereport__status=True)),
        absent_count=Count('attendancereport', filter=Q(attendancereport__status=False)),
        leave_count=Count('leavereportstudent', filter=Q(leavereportstudent__leave_status=1))
    ).values('admin__username', 'present_count', 'absent_count', 'leave_count')

    student_name_list = [item['admin__username'] for item in student_attendance_data]
    attendance_present_list_student = [item['present_count'] for item in student_attendance_data]

    # Total "absences" is a sum of unapproved attendance and approved leaves.

    attendance_absent_list_student = [item['absent_count'] + item['leave_count'] for item in student_attendance_data]

    # --- 3. Prepare Context and Render Template ---

    context = {
        # --- Data for Summary Cards ---
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


def add_staff(request):
    return render(request, "hod_template/add_staff_template.html")


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
        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                  first_name=first_name, last_name=last_name, user_type='2')
            # The user's Staff profile is created by a signal.
            # We need to fetch that profile, update it, and then save it.
            staff_profile = user.staff
            staff_profile.address = address
            staff_profile.save()
            messages.success(request, "Successfully Added Staff")
            return HttpResponseRedirect(reverse("add_staff"))
        except Exception as e:
            messages.error(request, f"Failed to Add Staff: {e}")
            return HttpResponseRedirect(reverse("add_staff"))


def add_course(request):
    return render(request, "hod_template/add_course_template.html")


def add_course_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        course = request.POST.get("course")
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Successfully Added Course")
            return HttpResponseRedirect(reverse("add_course"))
        except Exception as e:
            messages.error(request, f"Failed to Add Course: {e}")
            return HttpResponseRedirect(reverse("add_course"))


def add_student(request):
    form = AddStudentForm()
    return render(request, "hod_template/add_student_template.html", {"form": form})


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

            # Handle file upload safely
            profile_picture = request.FILES.get("profile_picture", None)
            profile_picture_url = ""
            if profile_picture:
                fileStorage = FileSystemStorage()
                filename = fileStorage.save(profile_picture.name, profile_picture)
                profile_picture_url = fileStorage.url(filename)

            try:
                user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                      first_name=first_name, last_name=last_name, user_type='3')
                user.student.address = address
                # Assign the object directly to the model field
                user.student.course = course_id
                # Assign the object directly to the model field
                user.student.session_year = session_year_id
                user.student.gender = sex
                user.student.profile_picture = profile_picture_url
                user.save()
                messages.success(request, "Successfully Added Student")
                return HttpResponseRedirect(reverse("add_student"))
            except Exception as e:
                messages.error(request, f"Failed to Add Student: {e}")
                return HttpResponseRedirect(reverse("add_student"))
        else:
            form = AddStudentForm(request.POST)
            messages.error(request, "Please correct the errors below")
            return render(request, "hod_template/add_student_template.html", {"form": form})


def add_subject(request):
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/add_subject_template.html", {"staffs": staffs, "courses": courses})


def add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_name = request.POST.get("subject_name")
        course_id = request.POST.get("course")
        course = Courses.objects.get(id=course_id)
        staff_id = request.POST.get("staff")
        staff = CustomUser.objects.get(id=staff_id)

        try:
            subject = Subject(subject_name=subject_name, course=course, staff=staff)
            subject.save()
            messages.success(request, "Successfully Added Subject")
            return HttpResponseRedirect(reverse("add_subject"))
        except Exception as e:
            messages.error(request, f"Failed to Add Subject: {e}")
            return HttpResponseRedirect(reverse("add_subject"))


def manage_staff(request):
    staffs = Staff.objects.all()
    return render(request, "hod_template/manage_staff_template.html", {"staffs": staffs})


def manage_student(request):
    students = Student.objects.all()
    return render(request, "hod_template/manage_student_template.html", {"students": students})


def manage_course(request):
    courses = Courses.objects.all()
    return render(request, "hod_template/manage_course_template.html", {"courses": courses})


def manage_subject(request):
    # Use select_related to pre-fetch related Course and Staff (CustomUser) objects.
    # This is much more efficient than fetching them one by one in the template.
    subjects = Subject.objects.select_related('course', 'staff').all()
    return render(request, "hod_template/manage_subject_template.html", {"subjects": subjects})


def edit_staff(request, staff_id):
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

        try:
            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()

            staff_model = Staff.objects.get(admin=staff_id)
            staff_model.address = address
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

            if request.FILES.get('profile_picture', False):
                profile_picture = request.FILES.get("profile_picture")
                fileStorage = FileSystemStorage()
                filename = fileStorage.save(profile_picture.name, profile_picture)
                profile_picture_url = fileStorage.url(filename)
            else:
                profile_picture_url = None

            user = CustomUser.objects.get(id=student_id)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.save()

            student = Student.objects.get(admin=student_id)
            student.address = address
            student.session_year = session_year_id
            student.gender = sex
            student.course = course_id

            if profile_picture_url is not None:
                student.profile_picture = profile_picture_url

            student.save()
            del request.session['student_id']

            messages.success(request, "Successfully Edited Student")
            return HttpResponseRedirect(reverse("manage_student"))
        else:
            form = EditStudentForm(request.POST)
            student = Student.objects.get(admin=student_id)
            return render(request, "hod_template/edit_student_template.html",
                          {"form": form, "id": student_id, "username": student.admin.username})


def edit_subject(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/edit_subject_template.html",
                  {"subject": subject, "staffs": staffs, "courses": courses, "id": subject_id, })


def edit_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id = request.POST.get("subject_id")
        subject_name = request.POST.get("subject_name")
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            subject = Subject.objects.get(id=subject_id)
            subject.subject_name = subject_name
            staff = CustomUser.objects.get(id=staff_id)
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
            session_year = SessionYear(session_start_year=session_start_year, session_end_year=session_end_year)
            session_year.save()
            messages.success(request, "Successfully Added Session")
            return HttpResponseRedirect(reverse("manage_session"))
        except Exception as e:
            messages.error(request, f"Failed to Add Session: {e}")
            return HttpResponseRedirect(reverse("manage_session"))


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
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
    subjects = Subject.objects.all()
    session_year_id = SessionYear.objects.all()
    return render(request, "hod_template/admin_view_attendance_template.html",
                  {"subjects": subjects, "session_year_id": session_year_id})


@csrf_exempt
def admin_get_attendance_dates(request):
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
def admin_get_student_attendance(request):
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

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name

            # An HOD user does not have a student profile, so we should not try to access it.
            # The logic for updating a student's profile picture should be in a
            # separate view accessible only to students.
            # if request.FILES.get('profile_picture'):
            #     profile_picture = request.FILES.get("profile_picture")
            #     fileStorage = FileSystemStorage()
            #     filename = fileStorage.save(profile_picture.name, profile_picture)
            #     profile_picture_url = fileStorage.url(filename)
            #     customuser.student.profile_picture = profile_picture_url

            if password is not None and password != "":
                customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Edited Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except Exception as e:
            messages.error(request, f"Failed to Edit Profile: {e}")
            return HttpResponseRedirect(reverse("admin_profile"))
