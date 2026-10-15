from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
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
# USER PROFILE — EDIT PROFILE
# ============================================================

PROFILE_IMAGE_MAX_MB = 5


class EditProfileForm(forms.ModelForm):
    """Edit the signed-in user's own name and email (the login identity)."""

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Your first name',
            'autocomplete': 'given-name',
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Your last name',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', 'id_profile_%s')
        super().__init__(*args, **kwargs)

    def clean_first_name(self):
        return (self.cleaned_data.get('first_name') or '').strip()

    def clean_last_name(self):
        return (self.cleaned_data.get('last_name') or '').strip()

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data.get('email') or '').strip()
        clash = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('Another account already uses this email address.')
        return email


# ============================================================
# SETTINGS — CHANGE PASSWORD
# ============================================================

class ChangePasswordForm(PasswordChangeForm):
    """Settings > Security: Django's PasswordChangeForm (current password
    check, matching confirmation, AUTH_PASSWORD_VALIDATORS, secure save)."""

    def __init__(self, user=None, *args, **kwargs):
        kwargs.setdefault('auto_id', 'id_changepw_%s')
        super().__init__(user, *args, **kwargs)
        for name in ('old_password', 'new_password1', 'new_password2'):
            self.fields[name].widget.attrs['class'] = 'pw-input'


class ProfileImgForm(forms.ModelForm):
    picture = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.gif,.webp'})
    )

    class Meta:
        model = ProfileImg
        fields = ['picture']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', 'id_profile_%s')
        super().__init__(*args, **kwargs)

    def clean_picture(self):
        picture = self.cleaned_data.get('picture')
        if picture and getattr(picture, 'size', 0) > PROFILE_IMAGE_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f'Profile pictures must be {PROFILE_IMAGE_MAX_MB} MB or smaller.'
            )
        return picture


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
