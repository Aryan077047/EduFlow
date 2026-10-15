from django.db import models
from django.conf import settings


UserModel = settings.AUTH_USER_MODEL


class Course(models.Model):

    COURSE_CATEGORY = (
        ('math', 'Mathematics'),
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('english', 'English'),
        ('computer', 'Computer Science'),
        ('programming', 'Programming'),
        ('database', 'Database'),
        ('networking', 'Networking'),
        ('ai', 'Artificial Intelligence'),
        ('machine_learning', 'Machine Learning'),
        ('web_development', 'Web Development'),
        ('mobile_development', 'Mobile Development'),
        ('cyber_security', 'Cyber Security'),
        ('statistics', 'Statistics'),
        ('accounting', 'Accounting'),
        ('finance', 'Finance'),
        ('economics', 'Economics'),
        ('history', 'History'),
        ('geography', 'Geography'),
        ('psychology', 'Psychology'),
        ('philosophy', 'Philosophy'),
        ('business', 'Business'),
        ('marketing', 'Marketing'),
        ('graphic_design', 'Graphic Design'),
        ('flutter', 'Flutter'),
        ('django', 'Django'),
        ('python', 'Python'),
        ('java', 'Java'),
        ('csharp', 'C#'),
    )

    COURSE_LEVEL = (
        ('beginner', 'Beginner'),
        ('intermediat', 'Intermediat'),
        ('advance', 'Advance'),
    )
    student = models.ForeignKey(UserModel, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=COURSE_CATEGORY
    )

    level = models.CharField(
        max_length=50,
        choices=COURSE_LEVEL
    )
    Course_price = models.IntegerField()

    vedio = models.FileField(upload_to='course_vedio/')

    description = models.TextField()

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Kept on the original table so no data migration was needed
        # when the model moved out of the legacy `admmitions` app.
        db_table = 'admmitions_course'

    def __str__(self):
        return self.title

    @property
    def category_display(self):
        return dict(self.COURSE_CATEGORY).get(self.category, self.category)

    @property
    def level_display(self):
        return dict(self.COURSE_LEVEL).get(self.level, self.level)

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def view_count(self):
        return 0


class Playlist(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='playlists'
    )
    video = models.FileField(
        upload_to='course_videos/'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'admmitions_playlist'

    def __str__(self):
        return self.video.name if self.video else "Untitled"


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video = models.FileField(
        upload_to='course_videos/',
        blank=True,
        null=True
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        db_table = 'admmitions_lesson'

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class TeacherApplication(models.Model):

    EXPERTISE_CHOICES = (
        ('mathematics', 'Mathematics'),
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('english', 'English'),
        ('computer_science', 'Computer Science'),
        ('information_technology', 'Information Technology (IT)'),
        ('programming', 'Programming'),
        ('web_development', 'Web Development'),
        ('mobile_development', 'Mobile Development'),
        ('cyber_security', 'Cyber Security'),
        ('networking', 'Networking'),
        ('database', 'Database'),
        ('artificial_intelligence', 'Artificial Intelligence'),
        ('machine_learning', 'Machine Learning'),
        ('data_science', 'Data Science'),
        ('graphic_design', 'Graphic Design'),
        ('business', 'Business'),
        ('marketing', 'Marketing'),
        ('accounting', 'Accounting'),
        ('finance', 'Finance'),
        ('economics', 'Economics'),
        ('history', 'History'),
        ('geography', 'Geography'),
    )

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='teacher_applications'
    )

    experience = models.CharField(max_length=200)

    expertise = models.CharField(
        max_length=50,
        choices=EXPERTISE_CHOICES
    )

    c_v = models.FileField(upload_to='teacher_cv/')

    portfolio = models.URLField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )

    reason = models.TextField()

    class Meta:
        db_table = 'admmitions_teacherapplication'


# ============================================================
# QUIZ MODELS
# ============================================================

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    ATTEMPT_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('Unlimited', 'Unlimited'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    teacher = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='created_quizzes'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    chapter = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    duration = models.PositiveIntegerField(default=30)
    passing_score = models.PositiveIntegerField(default=70)
    attempts_allowed = models.CharField(max_length=20, choices=ATTEMPT_CHOICES, default='2')

    # Toggles from the quiz builder UI
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=True)
    show_answers = models.BooleanField(default=True)
    time_limit = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'admmitions_quiz'

    def __str__(self):
        return self.title

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    @property
    def total_questions(self):
        return self.questions.count()


class Question(models.Model):
    TYPE_CHOICES = [
        ('mc', 'Multiple Choice'),
        ('explain', 'Explanation'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='mc')
    text = models.TextField()
    points = models.PositiveIntegerField(default=2)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        db_table = 'admmitions_question'

    def __str__(self):
        return f"Q{self.order + 1}: {self.text[:50]}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        db_table = 'admmitions_answer'

    def __str__(self):
        return self.text
