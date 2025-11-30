from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from student_management_app.forms import AdminSignupForm, StaffSignupForm
from student_management_app.models import CustomUser, Courses, SessionYear


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


def showFirebaseJS(request):
    data = 'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
           'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
           'var firebaseConfig = {' \
           '        apiKey: "YOUR_API_KEY",' \
           '        authDomain: "FIREBASE_AUTH_URL",' \
           '        databaseURL: "FIREBASE_DATABASE_URL",' \
           '        projectId: "FIREBASE_PROJECT_ID",' \
           '        storageBucket: "FIREBASE_STORAGE_BUCKET_URL",' \
           '        messagingSenderId: "FIREBASE_SENDER_ID",' \
           '        appId: "FIREBASE_APP_ID",' \
           '        measurementId: "FIREBASE_MEASUREMENT_ID"' \
           ' };' \
           'firebase.initializeApp(firebaseConfig);' \
           'const messaging=firebase.messaging();' \
           'messaging.setBackgroundMessageHandler(function (payload) {' \
           '    console.log(payload);' \
           '    const notification=JSON.parse(payload);' \
           '    const notificationOption={' \
           '        body:notification.body,' \
           '        icon:notification.icon' \
           '    };' \
           '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
           '});'

    return HttpResponse(data, content_type='application/javascript')


def admin_signup(request):
    form = AdminSignupForm()
    return render(request, 'admin_signup_page.html', {'form': form})


def staff_signup(request):
    form = StaffSignupForm()
    return render(request, 'staff_signup_page.html', {'form': form})


def student_signup(request):
    courses = Courses.objects.all()
    session_years = SessionYear.objects.all()
    return render(request, 'student_signup_page.html', {'courses': courses, 'session_years': session_years})


def do_admin_signup(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('admin_signup'))

    form = AdminSignupForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        try:
            user = CustomUser.objects.create_user(username=username, email=email, password=password, user_type='1')
            # The user profile (AdminHOD) is created automatically by a signal
            user.save()
            messages.success(request, "Successfully Created Admin Account. Please log in.")
            return HttpResponseRedirect(reverse("show_login"))
        except Exception as e:
            messages.error(request, f"Failed to Create Admin Account: {e}")
            return HttpResponseRedirect(reverse("admin_signup"))
    else:
        # Re-render the page with the form containing errors
        return render(request, 'admin_signup_page.html', {'form': form})


def do_staff_signup(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('staff_signup'))

    form = StaffSignupForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        address = form.cleaned_data.get('address')
        try:
            user = CustomUser.objects.create_user(username=username, email=email, password=password, user_type='2')
            user.staff.address = address
            user.save()
            messages.success(request, "Successfully Created Staff Account. Please log in.")
            return HttpResponseRedirect(reverse("show_login"))
        except Exception as e:
            messages.error(request, f"Failed to Create Staff Account: {e}")
            return HttpResponseRedirect(reverse("staff_signup"))
    else:
        return render(request, 'staff_signup_page.html', {'form': form})


def do_student_signup(request):
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")
    address = request.POST.get("address")
    session_year_id = request.POST.get("session_year")
    course_id = request.POST.get("course")
    sex = request.POST.get("sex")

    profile_pic = request.FILES['profile_pic']
    fs = FileSystemStorage()
    filename = fs.save(profile_pic.name, profile_pic)
    profile_pic_url = fs.url(filename)

    try:
        user = CustomUser.objects.create_user(first_name=first_name, last_name=last_name, username=username,
                                              password=password, email=email, user_type='3')
        user.student.address = address
        course_obj = Courses.objects.get(id=course_id)
        user.student.course_id = course_obj
        session_year = SessionYear.object.get(id=session_year_id)
        user.student.session_year_id = session_year
        user.student.gender = sex
        user.student.profile_pic = profile_pic_url
        user.save()
        messages.success(request, "Successfully Created Student Account")
        return HttpResponseRedirect(reverse("show_login"))
    except:
        messages.error(request, "Failed to Create Student Account")
        return HttpResponseRedirect(reverse("show_login"))
