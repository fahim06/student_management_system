from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from student_management_app.models import CustomUser, Courses


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
