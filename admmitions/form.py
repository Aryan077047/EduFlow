from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth.password_validation import validate_password
from .models import Course, User , TeacherApplication , ProfileImg , Playlist
from django.contrib.auth.forms import UserCreationForm




class teacher_form(UserCreationForm):
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class':'form-control'})
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    


    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class':'form-control'})
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class':'form-control'})
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class':'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name','email', 'password1', 'password2',]
        




class course_form(forms.ModelForm):

    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class':'input-field'
        })
    )

    category = forms.ChoiceField(
        choices=Course.COURSE_CATEGORY,
        widget=forms.Select(attrs={
            'class':'select-field'
        })
    )

    level = forms.ChoiceField(
        choices=Course.COURSE_LEVEL,
        widget=forms.Select(attrs={
            'class':'select-field'
        })
    )

    Course_price = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class':'input-field',
            'placeholder':'$49'
        })
    )

    vedio = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class':'input-field'
        })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class':'textarea-field',
            'placeholder':'Write detailed course description...'
        })
    )

    class Meta:
        model = Course
        fields = ['title','category','level','Course_price','vedio','description']

    def clean_vedio(self):
        video = self.cleaned_data.get('vedio')
        if video:
            return video
        existing = getattr(self.instance, 'vedio', None)
        if existing:
            return existing
        raise forms.ValidationError('Please upload a course video.')
        
        
        

class TeacherApplicationForm(forms.ModelForm):
    class Meta:
        model = TeacherApplication
        fields = ['experience', 'expertise', 'portfolio','c_v','reason']
        
        

        
class ProfileImgForm(forms.ModelForm):
    picture = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )

    class Meta:
        model = ProfileImg
        fields = ['picture']
        
        
        
        
        
        
# Extensions are listed explicitly because accept="video/*" alone makes the
# Windows file dialog hide containers it does not recognise (.mkv, .avi, .wmv,
# .flv, some .mov), leaving the file impossible to select.
VIDEO_ACCEPT = ('video/*,.mp4,.webm,.ogv,.ogg,.mov,.mkv,.avi,.wmv,'
                '.flv,.m4v,.mpg,.mpeg,.3gp')


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['video']
        widgets = {
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': VIDEO_ACCEPT,
            }),
        }


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
            'placeholder': 'Confirm new password',
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