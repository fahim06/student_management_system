from django import forms
from django.contrib.auth import get_user_model
from django.forms import ChoiceField

from student_management_app.models import Courses, SessionYear, Subject, Student

User = get_user_model()

class ChoiceNoValidation(ChoiceField):
    def validate(self, value):
        pass


class DateInput(forms.DateInput):
    input_type = 'date'


class AdminSignupForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username", "autocomplete": "off"})
    )
    email = forms.EmailField(
        label='Email',
        max_length=50,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email", "autocomplete": "off"})
    )
    password = forms.CharField(
        label='Password',
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password2"):
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data


class StaffSignupForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username", "autocomplete": "off"})
    )
    email = forms.EmailField(
        label='Email',
        max_length=50,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email", "autocomplete": "off"})
    )
    password = forms.CharField(
        label='Password',
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"})
    )
    address = forms.CharField(
        label='Address',
        max_length=255,
        widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Address", "rows": 3})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password2"):
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data


class AddStudentForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=50,
                             widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "off"}))
    password = forms.CharField(label='Password', max_length=50,
                               widget=forms.PasswordInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label='First Name', max_length=50,
                                 widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label='Last Name', max_length=50,
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label='Username', max_length=50,
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    address = forms.CharField(label='Address', max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))

    # Use ModelChoiceField to dynamically load choices from the database
    # This avoids running a query when the module is imported.
    course = forms.ModelChoiceField(
        queryset=Courses.objects.all(),
        label="Course",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    gender_choice = (('Male', 'Male'), ('Female', 'Female'))
    sex = forms.ChoiceField(label='Sex', choices=gender_choice, widget=forms.Select(attrs={"class": "form-control"}))
    session_year_id = forms.ModelChoiceField(queryset=SessionYear.objects.all(), label="Session Year",
                                             widget=forms.Select(attrs={"class": "form-control"}))
    profile_picture = forms.ImageField(label='Profile Picture', widget=forms.FileInput(attrs={"class": "form-control"}))


class EditStudentForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=50, widget=forms.EmailInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label='First Name', max_length=50,
                                 widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label='Last Name', max_length=50,
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label='Username', max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label='Address', max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))

    # Use ModelChoiceField here as well for consistency and robustness.
    course = forms.ModelChoiceField(
        queryset=Courses.objects.all(),
        label="Course",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    gender_choice = (('Male', 'Male'), ('Female', 'Female'))
    sex = forms.ChoiceField(label='Sex', choices=gender_choice, widget=forms.Select(attrs={"class": "form-control"}))
    session_year_id = forms.ModelChoiceField(
        queryset=SessionYear.objects.all(),
        label="Session Year",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    profile_picture = forms.ImageField(label='Profile Picture', widget=forms.FileInput(attrs={"class": "form-control"}),
                                       required=False)


class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.staff_id = kwargs.pop("staff_id")
        super(EditResultForm, self).__init__(*args, **kwargs)

        # Fetch Subjects dynamically
        subject_list = []
        try:
            subjects = Subject.objects.filter(staff_id=self.staff_id)
            for subject in subjects:
                subject_single = (subject.id, subject.subject_name)
                subject_list.append(subject_single)
        except Exception:
            subject_list = []
        self.fields['subject_id'].choices = subject_list

        # Fetch Session Years dynamically
        session_list = []
        try:
            sessions = SessionYear.objects.all()
            for session in sessions:
                session_single = (session.id, f"{session.session_start_year} TO {session.session_end_year}")
                session_list.append(session_single)
        except Exception:
            session_list = []
        self.fields['session_id'].choices = session_list

        # --- Add this block to populate the student dropdown ---
        # This will pre-populate the student list based on the first subject and session.
        # The list will be updated dynamically via JavaScript when the user changes selections.
        student_list = []
        try:
            if subject_list and session_list:
                first_subject = Subject.objects.get(id=subject_list[0][0])
                first_session = SessionYear.objects.get(id=session_list[0][0])
                students = Student.objects.filter(course_id=first_subject.course_id,
                                                  session_year_id=first_session.id)
                for student in students:
                    student_single = (student.admin.id, f"{student.admin.first_name} {student.admin.last_name}")
                    student_list.append(student_single)
        except Exception:
            student_list = []
        self.fields['student_ids'].choices = student_list
        # --- End of new block ---

    subject_id = forms.ChoiceField(label='Subject', widget=forms.Select(attrs={"class": "form-control"}))
    session_id = forms.ChoiceField(label='Session Year', widget=forms.Select(attrs={"class": "form-control"}))
    student_ids = ChoiceNoValidation(label="Student", widget=forms.Select(attrs={"class": "form-control"}))
    assignment_marks = forms.FloatField(label='Assignment Marks',
                                        widget=forms.NumberInput(attrs={"class": "form-control"}))
    exam_marks = forms.FloatField(label='Exam Marks',
                                  widget=forms.NumberInput(attrs={"class": "form-control"}))
