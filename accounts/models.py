from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


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
    username = None

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    # Language chosen on the Settings page (en / fa / ps). Used by the
    # i18n context processor when rendering menus and buttons.
    USER_LANGUAGES = (
        ('en', 'English'),
        ('fa', 'Persian (Dari)'),
        ('ps', 'Pashto'),
    )
    language = models.CharField(
        max_length=5, choices=USER_LANGUAGES, default='en',
    )
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        # Kept on the original table so no data migration was needed
        # when the model moved out of the legacy `admmitions` app.
        db_table = 'admmitions_user'


class ProfileImg(models.Model):
    picture = models.ImageField(upload_to='profile_images/')
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'admmitions_profileimg'


# ============================================================
# PASSWORD RESET - EMAIL OTP
# ============================================================

class PasswordResetOTP(models.Model):
    """One issued OTP code. The plaintext code is emailed and never stored -
    only its hash, so a database leak cannot be replayed against accounts."""

    OTP_LENGTH = 6
    OTP_TTL_MINUTES = 10
    MAX_VERIFY_ATTEMPTS = 5
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='password_reset_otps'
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        db_table = 'admmitions_passwordresetotp'

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


class AIConversation(models.Model):
    """One named chat in the study assistant's sidebar. Each conversation
    holds an ordered list of AIChatMessage turns and can be re-opened,
    cleared or deleted by its owner at any time."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ai_conversations'
    )
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'AI conversation'
        verbose_name_plural = 'AI conversations'
        db_table = 'accounts_aiconversation'

    def __str__(self):
        return self.title


class AIChatMessage(models.Model):
    """One turn of the AI study assistant: the student/teacher's question and
    the assistant's reply, grouped inside an AIConversation so past chats are
    listed in the sidebar and can be re-opened."""

    ROLE_CHOICES = (('user', 'Question'), ('assistant', 'Answer'))

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ai_chat_messages'
    )
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'AI chat message'
        verbose_name_plural = 'AI chat messages'
        db_table = 'admmitions_aichatmessage'

    def __str__(self):
        return f'{self.user.email} - {self.role}: {self.content[:40]}'
