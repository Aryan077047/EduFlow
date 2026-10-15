from django import forms

from .models import Course, Playlist, TeacherApplication


class course_form(forms.ModelForm):

    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-field'
        })
    )

    category = forms.ChoiceField(
        choices=Course.COURSE_CATEGORY,
        widget=forms.Select(attrs={
            'class': 'select-field'
        })
    )

    level = forms.ChoiceField(
        choices=Course.COURSE_LEVEL,
        widget=forms.Select(attrs={
            'class': 'select-field'
        })
    )

    Course_price = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'input-field',
            'placeholder': '$49'
        })
    )

    vedio = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field'
        })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea-field',
            'placeholder': 'Write detailed course description...'
        })
    )

    class Meta:
        model = Course
        fields = ['title', 'category', 'level', 'Course_price', 'vedio', 'description']

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
        fields = ['experience', 'expertise', 'portfolio', 'c_v', 'reason']


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
