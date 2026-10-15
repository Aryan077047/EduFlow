from django.db import models
from django.conf import settings

from teacher.models import Answer, Course, Question, Quiz


UserModel = settings.AUTH_USER_MODEL


class Enrollment(models.Model):
    student = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        # Kept on the original table so no data migration was needed
        # when the model moved out of the legacy `admmitions` app.
        db_table = 'admmitions_enrollment'


class CourseOrder(models.Model):
    student = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    class Meta:
        db_table = 'admmitions_courseorder'

    @property
    def name(self):
        return self.course.title

    @property
    def price(self):
        return float(self.course.Course_price)


class Post(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admmitions_post'


class Comment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'admmitions_comment'


class Like(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user')
        db_table = 'admmitions_like'


# ============================================================
# QUIZ ATTEMPT & STUDENT ANSWER
# ============================================================

class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted',   'Submitted'),
        ('graded',      'Graded'),
    ]

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='attempts'
    )
    student = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name='quiz_attempts'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Auto-graded score (MC questions)
    score = models.FloatField(default=0)

    # Manual score (explanation questions)
    manual_score = models.FloatField(default=0)

    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='in_progress'
    )
    graded_by = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='graded_attempts',
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at', '-started_at']
        db_table = 'admmitions_quizattempt'

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
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name='answers'
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE
    )

    # For MC questions
    selected = models.ForeignKey(
        Answer, on_delete=models.SET_NULL, null=True, blank=True
    )

    # For 'explain' questions
    text_answer = models.TextField(blank=True)

    is_correct = models.BooleanField(default=False)
    points_awarded = models.FloatField(default=0)
    teacher_feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['question__order']
        db_table = 'admmitions_studentanswer'

    def __str__(self):
        return f"{self.attempt.student.email} · Q{self.question.order + 1}"
