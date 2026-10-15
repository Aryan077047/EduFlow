from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import ProfileImg, User


class teacher_form(UserCreationForm):
    """Account creation form for new teachers (kept name for compatibility)."""

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', ]


# ============================================================
# USER PROFILE — EDIT PROFILE (name fields; email is login identity)
# ============================================================

class EditProfileForm(forms.ModelForm):
    """Edit the signed-in user's own profile fields. Email is the login
    identity (USERNAME_FIELD), so it stays read-only here by design."""

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your first name',
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your last name',
        }),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


# ============================================================
# SETTINGS — CHANGE PASSWORD
# ============================================================

class ChangePasswordForm(forms.Form):
    """Settings > Security: change the signed-in user's password.

    Requires the current password, enforces Django's configured password
    validators on the new one, and keeps the session (no re-auth needed).
    Field names follow Django's PasswordChangeForm conventions.
    """

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
        }),
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        # Self-registration is the default so the form validates standalone;
        # views pass user=request.user for the real check.
        kwargs.setdefault('auto_id', 'id_changepw_%s')
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if self.user is not None and not self.user.check_password(old):
            raise forms.ValidationError('Your current password was entered incorrectly.')
        return old

    def clean_new_password2(self):
        p1 = self.cleaned_data.get('new_password1')
        p2 = self.cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('The two password fields did not match.')
        return p2

    def _post_clean(self):
        password = self.cleaned_data.get('new_password1')
        if not password:
            return
        user = self.user or User()
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            self.add_error('new_password1', exc)


class ProfileImgForm(forms.ModelForm):
    picture = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )

    class Meta:
        model = ProfileImg
        fields = ['picture']


# ============================================================
# PASSWORD RESET - EMAIL OTP
# ============================================================

class ForgotPasswordForm(forms.Form):
    """Step 1: ask for the account email."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
            'autofocus': 'autofocus',
        })
    )


class OTPVerifyForm(forms.Form):
    """Step 2: check the emailed 6-digit code."""

    code = forms.CharField(
        min_length=6,
        max_length=6,
        strip=True,
        widget=forms.TextInput(attrs={
            'class': 'otp-input',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'autofocus': 'autofocus',
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit():
            raise forms.ValidationError('The code must be 6 digits.')
        return code


class SetPasswordForm(forms.Form):
    """Step 3: choose the new password."""

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
            'autofocus': 'autofocus',
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        })
    )

    def clean_new_password2(self):
        p1 = self.cleaned_data.get('new_password1')
        p2 = self.cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('The two passwords do not match.')
        return p2

    def _post_clean(self):
        password = self.cleaned_data.get('new_password1')
        if not password:
            return
        try:
            validate_password(password)
        except ValidationError as exc:
            self.add_error('new_password1', exc)
