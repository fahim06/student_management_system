from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class LoginCheckMiddleWare(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):
        module_name = view_func.__module__
        user = request.user
        if user.is_authenticated:
            if user.user_type == "1":
                if module_name == "student_management_app.hodViews":
                    pass
                elif module_name == "student_management_app.views" or module_name == "django.views.static":
                    pass
                else:
                    return HttpResponseRedirect(reverse("admin_home"))
            elif user.user_type == "2":
                if module_name == "student_management_app.staffViews" or module_name == "django.views.static":
                    pass
                elif module_name == "student_management_app.views":
                    pass
                else:
                    return HttpResponseRedirect(reverse("staff_home"))
            elif user.user_type == "3":
                if module_name == "student_management_app.studentViews" or module_name == "django.views.static":
                    pass
                elif module_name == "student_management_app.views":
                    pass
                else:
                    return HttpResponseRedirect(reverse("student_home"))
            else:
                return HttpResponseRedirect(reverse("show_login"))
        else:
            if request.path == reverse("show_login") or request.path == reverse(
                    "login") or module_name == "django.contrib.auth.views":
                pass
            else:
                return HttpResponseRedirect(reverse("show_login"))
