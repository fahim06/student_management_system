import datetime

from django.shortcuts import render

from student_management_app.models import Subject, Student, CustomUser, Attendance, AttendanceReport


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
