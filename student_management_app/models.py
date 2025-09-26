from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class SessionYear(models.Model):
    session_start_year = models.DateField()
    session_end_year = models.DateField()

    def __str__(self):
        """
        Return a formatted string for the session year range.
        """
        return f"{self.session_start_year.strftime('%Y')} to {self.session_end_year.strftime('%Y')}"

class CustomUser(AbstractUser):
    user_type_data = ((1, "HOD"), (2, "STAFF"), (3, "STUDENT"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)


class AdminHOD(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username


class Staff(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username


class Courses(models.Model):
    course_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return the name of the course for display purposes.
        """
        return self.course_name


class Subject(models.Model):
    subject_name = models.CharField(max_length=255)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1)
    staff = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject_name


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=255)
    profile_picture = models.FileField()
    address = models.TextField()
    course = models.ForeignKey(Courses, on_delete=models.DO_NOTHING, null=True)
    session_year = models.ForeignKey(SessionYear, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username


class Attendance(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    attendance_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    session_year = models.ForeignKey(SessionYear, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedBackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedBackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == '1':
            AdminHOD.objects.create(admin=instance)
        elif instance.user_type == '2':
            Staff.objects.create(admin=instance, address="")
        elif instance.user_type == '3':
            # Avoid hardcoding IDs. It's better to let them be null and set later.
            # This also prevents errors if Course or SessionYear with ID=1 doesn't exist.
            Student.objects.create(admin=instance,
                                   address="", profile_picture="", gender="")
    else:
        # If the user is updated, save the related profile
        try:
            if instance.user_type == '1':
                instance.adminhod.save()
            elif instance.user_type == '2':
                instance.staff.save()
            elif instance.user_type == '3':
                instance.student.save()
        except:
            # This can happen if the profile was deleted manually.
            # In this case, we can re-create it.
            create_user_profile(sender, instance, created=True, **kwargs)
