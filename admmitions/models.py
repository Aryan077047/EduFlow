from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
# Create your models here.




class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)
    


    

class User(AbstractUser):
    username=None
    
    
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES,default='student' )
    email=models.EmailField(unique=True)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=[]
    objects = UserManager()
    
    
    
    
    
    
    
    
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

    COURSE_LEVEL=(
        ('beginner','Beginner'),
        ('intermediat','Intermediat'),
        ('advance','Advance'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=COURSE_CATEGORY
    )
    
    level= models.CharField(
        max_length=50,
        choices=COURSE_LEVEL
    )
    Course_price=models.IntegerField()
    
    vedio=models.FileField(upload_to='course_vedio/')

    description = models.TextField()

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)

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
        return 0   # اگر مدل View نداری
    
    
    
    
    
    
    

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

    user = models.ForeignKey(   # ← از OneToOne به ForeignKey تغییر بده
        User,
        on_delete=models.CASCADE,
        related_name='teacher_applications'
    )


    experience = models.CharField(max_length=200)

    expertise = models.CharField(
        max_length=50,
        choices=EXPERTISE_CHOICES
    )
    
    c_v= models.FileField(upload_to='teacher_cv/')


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
    
    reason=models.TextField()
    
    
    
    

class ProfileImg(models.Model):
    picture = models.ImageField(upload_to='profile_images/')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    
    
    

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        
        
        
        
        
        
        
        
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

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    
    

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        
        
class Like(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user')
        
        
        
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
        User,
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

    # Toggles from your UI
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=True)
    show_answers = models.BooleanField(default=True)
    time_limit = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
   

    is_published = models.BooleanField(default=False)   # ✅ NEW
    published_at = models.DateTimeField(null=True, blank=True)  # ✅ NEW

  

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

    def __str__(self):
        return f"Q{self.order + 1}: {self.text[:50]}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text
    
    
    

# ============================================================
# QUIZ ATTEMPT & STUDENT ANSWER
# ============================================================

class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted',   'Submitted'),
        ('graded',      'Graded'),
    ]

    quiz         = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='attempts'
    )
    student      = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quiz_attempts'
    )
    started_at   = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Auto-graded score (MC questions)
    score        = models.FloatField(default=0)

    # Manual score (explanation questions)
    manual_score = models.FloatField(default=0)

    status       = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='in_progress'
    )
    graded_by    = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='graded_attempts',
    )
    graded_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at', '-started_at']

    def __str__(self):
        return f"{self.student.email} → {self.quiz.title}"

    # ---------- Helpers used by the teacher/student views ----------
    @property
    def total_score(self):
        return self.score + self.manual_score

    @property
    def percentage(self):
        total = self.quiz.total_points or 1
        return round((self.total_score / total) * 100, 1)

    @property
    def passed(self):
        return self.percentage >= self.quiz.passing_score


class StudentAnswer(models.Model):
    attempt   = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name='answers'
    )
    question  = models.ForeignKey(
        Question, on_delete=models.CASCADE
    )

    # For MC questions
    selected  = models.ForeignKey(
        Answer, on_delete=models.SET_NULL, null=True, blank=True
    )

    # For 'explain' questions
    text_answer = models.TextField(blank=True)

    is_correct      = models.BooleanField(default=False)
    points_awarded  = models.FloatField(default=0)
    teacher_feedback = models.TextField(blank=True)
    graded_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['question__order']

    def __str__(self):
        return f"{self.attempt.student.email} · Q{self.question.order + 1}"


# ============================================================
# PASSWORD RESET - EMAIL OTP
# ============================================================

class PasswordResetOTP(models.Model):
    """One issued OTP code. The plaintext code is emailed and never stored -
    only its hash, so a database leak cannot be replayed against accounts."""

    OTP_LENGTH            = 6
    OTP_TTL_MINUTES       = 10
    MAX_VERIFY_ATTEMPTS   = 5
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='password_reset_otps'
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)
    attempts   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.user.email} (expires {self.expires_at:%H:%M})'

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_locked(self):
        return self.attempts >= self.MAX_VERIFY_ATTEMPTS

    @property
    def is_usable(self):
        return not (self.is_used or self.is_expired or self.is_locked)

    def seconds_left(self):
        if self.is_expired:
            return 0
        return int((self.expires_at - timezone.now()).total_seconds())

    def set_code(self, raw_code):
        self.code_hash = make_password(raw_code)

    def check_code(self, raw_code):
        return check_password(raw_code, self.code_hash)

    def register_failed_attempt(self):
        self.attempts += 1
        self.save(update_fields=['attempts'])

    def consume(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])