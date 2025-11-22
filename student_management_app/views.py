from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse


def ShowLoginPage(request):
    """
    Renders the login page.
    """
    return render(request, "login_page.html")


def doLogin(request):
    """
    Handles the login process, including the "Remember Me" functionality.
    """
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user = authenticate(request, username=request.POST.get("email"),
                            password=request.POST.get("password"))
        if user is not None:
            login(request, user)

            # --- "Remember Me" Functionality ---
            if request.POST.get("remember"):
                # If "Remember Me" is checked, set the session to expire in 2 weeks (in seconds).
                request.session.set_expiry(1209600)
            else:
                # If not checked, the session will expire when the user closes the browser.
                request.session.set_expiry(0)

            # --- Role-based Redirection ---
            if user.user_type == "1":
                return HttpResponseRedirect(reverse("admin_home"))
            elif user.user_type == "2":
                return HttpResponseRedirect(reverse("staff_home"))
            elif user.user_type == "3":
                return HttpResponseRedirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid Login Details")
            return HttpResponseRedirect("/")


def GetUserDetails(request):
    if request.user is not None:
        return HttpResponse("User: " + request.user.email + " usertype: " + str(request.user.user_type))
    else:
        return HttpResponse("Please Login First")


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")