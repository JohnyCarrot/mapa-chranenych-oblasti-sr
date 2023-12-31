from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import date

from map.models import Profile, Map_settings


# Create your forms here.

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    location = forms.CharField(required=True, min_length=1, max_length=75, label="Adresa")
    date_of_birth = forms.DateField(required=True, label="Dátum narodenia")
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        if (dob.year + 18, dob.month, dob.day) > (today.year, today.month, today.day):
            raise forms.ValidationError('Registrácia nie je povolená osobám mladším ako 18 rokov.')
        return dob

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        dob = self.cleaned_data['date_of_birth']
        loc = self.cleaned_data['location']
        if commit:
            user.save()
        profil = Profile.objects.create(user=user,map_settings=Map_settings.objects.create())
        profil.birth_date = dob
        profil.location = loc
        profil.save()
        return user


class NewUserForm_valid_check(UserCreationForm):
    email = forms.EmailField(required=True)
    location = forms.CharField(required=True, min_length=1, max_length=75, label="Adresa")
    date_of_birth = forms.DateField(required=True, label="Dátum narodenia")
    class Meta:
        model = User
        fields = ("email",)

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        if (dob.year + 18, dob.month, dob.day) > (today.year, today.month, today.day):
            raise forms.ValidationError('Pôsobenie na platforme nie je povolené osobám mladším ako 18 rokov.')
        return dob
