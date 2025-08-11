from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from student_management_app.models import CustomUser


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
        except:
            messages.error(request, "Failed Added Staff")
            return HttpResponseRedirect("/add_staff")
