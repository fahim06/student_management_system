from django import forms

from student_management_app.models import Courses, SessionYear


class DateInput(forms.DateInput):
    input_type = 'date'


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
