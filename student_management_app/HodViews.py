from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from student_management_app.models import CustomUser, Courses, Staff, Subject, Student


def admin_home(request):
    return render(request, 'hod_template/home_content.html')


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
                                                  first_name=first_name, last_name=last_name, user_type=2)
            user.staff.address = address
            user.save()
            messages.success(request, "Successfully Added Staff")
            return HttpResponseRedirect("/add_staff")
        except Exception as e:
            messages.error(request, f"Failed to Add Staff: {e}")
            return HttpResponseRedirect("/add_staff")


def add_course(request):
    return render(request, "hod_template/add_course_template.html")


def add_course_save(request):
    if request.method != "POST":
        return HttpResponseRedirect("Method Not Allowed")
    else:
        course = request.POST.get("course")
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Successfully Added Course")
            return HttpResponseRedirect("/add_course")
        except Exception as e:
            messages.error(request, f"Failed to Add Course: {e}")
            return HttpResponseRedirect("/add_course")


def add_student(request):
    courses = Courses.objects.all()
    return render(request, "hod_template/add_student_template.html", {"courses": courses})


def add_student_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        address = request.POST.get("address")
        session_start = request.POST.get("session_start")
        session_end = request.POST.get("session_end")
        course_id = request.POST.get("course")
        sex = request.POST.get("sex")
        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email,
                                                  first_name=first_name, last_name=last_name, user_type=3)
            user.student.address = address
            course_obj = Courses.objects.get(id=course_id)
            user.student.course_id = course_obj
            # user.student.session_start_year = session_start
            # user.student.session_end_year = session_end

            start_datetime_naive = datetime.strptime(session_start, '%Y-%m-%d')
            user.student.session_start_year = timezone.make_aware(start_datetime_naive)
            end_datetime_naive = datetime.strptime(session_end, '%Y-%m-%d')
            user.student.session_end_year = timezone.make_aware(end_datetime_naive)

            user.student.gender = sex
            user.student.profile_picture = ""
            user.save()
            messages.success(request, "Successfully Added Student")
            return HttpResponseRedirect("/add_student")
        except Exception as e:
            messages.error(request, f"Failed to Add Student: {e}")
            return HttpResponseRedirect("/add_student")


def add_subject(request):
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_template/add_subject_template.html", {"staffs": staffs, "courses": courses})


def add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_name = request.POST.get("subject")
        course_id = request.POST.get("course")
        course = Courses.objects.get(id=course_id)
        staff_id = request.POST.get("staff")
        staff = CustomUser.objects.get(id=staff_id)

        try:
            subject = Subject(subject_name=subject_name, course_id=course, staff_id=staff)
            subject.save()
            messages.success(request, "Successfully Added Subject")
            return HttpResponseRedirect("/add_subject")
        except Exception as e:
            messages.error(request, f"Failed to Add Subject: {e}")
            return HttpResponseRedirect("/add_subject")


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
    subjects = Subject.objects.all()
    return render(request, "hod_template/manage_subject_template.html", {"subjects": subjects})


def edit_staff(request, staff_id):
    staff = Staff.objects.get(admin=staff_id)
    return render(request, "hod_template/edit_staff_template.html", {"staff": staff})


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
            return HttpResponseRedirect(f"/edit_staff/{staff_id}")
        except Exception as e:
            messages.error(request, f"Failed to Edit Staff: {e}")
            return HttpResponseRedirect(f"/edit_staff/{staff_id}")


def edit_student(request, student_id):
    courses = Courses.objects.all()
    student = Student.objects.get(admin=student_id)
    return render(request, "hod_template/edit_student_template.html", {"student": student, "courses": courses})


def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        student_id = request.POST.get("student_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        address = request.POST.get("address")
        session_start = request.POST.get("session_start")
        session_end = request.POST.get("session_end")
        course_id = request.POST.get("course")
        sex = request.POST.get("sex")

        try:
            user = CustomUser.objects.get(id=student_id)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.save()

            student = Student.objects.get(admin=student_id)
            student.address = address
            student.session_start_year = session_start
            student.session_end_year = session_end
            student.gender = sex

            course = Courses.objects.get(id=course_id)
            student.course_id = course
            student.save()

            messages.success(request, "Successfully Edited Student")
            return HttpResponseRedirect(f"/edit_student/{student_id}")
        except Exception as e:
            messages.error(request, f"Failed to Edit Student: {e}")
            return HttpResponseRedirect(f"/edit_student/{student_id}")
