import csv

from django.shortcuts import render, redirect, get_object_or_404
from .form import course_form, teacher_form, TeacherApplicationForm, ProfileImgForm, PlaylistForm
from .form import ForgotPasswordForm, OTPVerifyForm, SetPasswordForm
from django.conf import settings
from django.core.mail import send_mail
import secrets
from django.contrib.auth.decorators import login_required
from .models import Course, TeacherApplication, ProfileImg, Enrollment, Playlist, Lesson, Post, Comment, Like, Quiz, Question, Answer, QuizAttempt, StudentAnswer, PasswordResetOTP, AIChatMessage
from django.contrib.auth import login
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import os
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.db.models import Count, Q, Prefetch
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import logout
from .models import (
    User,
    Course,
    TeacherApplication,
    ProfileImg,
    Enrollment,
    Playlist,
    Lesson,
    Post,
    Comment,
    Like,
)
User = get_user_model()


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to view the admin dashboard.")
        return redirect('index')

    total_users      = User.objects.count()
    total_students   = User.objects.filter(role='student').count()
    total_teachers   = User.objects.filter(role='teacher').count()
    total_courses    = Course.objects.count()
    total_enrollments= Enrollment.objects.count()
    total_comments   = Comment.objects.count()
    total_likes      = Like.objects.count()
    total_lessons    = Lesson.objects.count()
    total_playlists  = Playlist.objects.count()

    pending_staff = TeacherApplication.objects.filter(status='pending').count()

    pending_staff_requests = (
        TeacherApplication.objects
        .filter(status='pending')
        .select_related('user')
        .order_by('-id')
    )

    students = (
        User.objects
        .filter(role='student')
        .annotate(enrolled_count=Count('enrollment'))
        .order_by('-date_joined')
    )

    teachers = (
        User.objects
        .filter(role='teacher')
        .annotate(courses_count=Count('course'))
        .order_by('-date_joined')
    )

    courses = (
        Course.objects
        .select_related('student')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
        .order_by('-id')
    )

    recent_users = (
        User.objects
        .order_by('-date_joined')[:8]
    )

    recent_courses = (
        Course.objects
        .select_related('student')
        .order_by('-id')[:8]
    )

    recent_comments = (
        Comment.objects
        .select_related('user', 'course')
        .order_by('-created_at')[:8]
    )

    recent_enrollments = (
        Enrollment.objects
        .select_related('student', 'course')
        .order_by('-enrolled_at')[:8]
    )

    today = timezone.now().date()
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Enrollment.objects.filter(enrolled_at__date=day).count()
        last_7_days.append({
            'day':   day.strftime('%a'),
            'date':  day.strftime('%Y-%m-%d'),
            'count': count,
        })

    top_courses = (
        Course.objects
        .annotate(likes_count=Count('likes'))
        .order_by('-likes_count')[:5]
    )

    top_teachers = (
        User.objects
        .filter(role='teacher')
        .annotate(courses_count=Count('course'))
        .order_by('-courses_count')[:5]
    )

    recent_approved = (
        TeacherApplication.objects
        .filter(status='approved')
        .select_related('user')
        .order_by('-id')[:5]
    )

    recent_rejected = (
        TeacherApplication.objects
        .filter(status='rejected')
        .select_related('user')
        .order_by('-id')[:5]
    )

    context = {
        'total_users':       total_users,
        'total_students':    total_students,
        'total_teachers':    total_teachers,
        'total_courses':     total_courses,
        'total_enrollments': total_enrollments,
        'total_comments':    total_comments,
        'total_likes':       total_likes,
        'total_lessons':     total_lessons,
        'total_playlists':   total_playlists,
        'pending_staff':     pending_staff,

        'pending_staff_requests': pending_staff_requests,

        'students': students,
        'teachers': teachers,
        'courses':  courses,

        'recent_users':        recent_users,
        'recent_courses':      recent_courses,
        'recent_comments':     recent_comments,
        'recent_enrollments':  recent_enrollments,

        'last_7_days': last_7_days,

        'top_courses':  top_courses,
        'top_teachers': top_teachers,

        'recent_approved': recent_approved,
        'recent_rejected': recent_rejected,

        'admin_user': request.user,
    }

    return render(request, 'dashboard.html', context)


@login_required
def approve_staff(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser only")

    application = get_object_or_404(TeacherApplication, pk=pk)
    application.status = 'approved'
    application.save()

    user = application.user
    user.role = 'teacher'
    user.is_staff = True
    user.save()

    return redirect('admin_dashboard')


@login_required
def reject_staff(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser only")

    application = get_object_or_404(TeacherApplication, pk=pk)
    application.status = 'rejected'
    application.save()

    return redirect('admin_dashboard')


def index(request):

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    courses = (
        Course.objects
        .select_related('student')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
        .order_by('id')
    )

    if request.user.is_authenticated:
        courses = courses.filter(Q(is_published=True) | Q(student=request.user))
    else:
        courses = courses.filter(is_published=True)

    courses = courses.prefetch_related(
        Prefetch(
            'comments',
            queryset=Comment.objects.select_related('user').order_by('-created_at'),
        )
    )

    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects
            .filter(student=request.user, course__in=courses)
            .values_list('course_id', flat=True)
        )

    course_info = []
    for c in courses:
        c.is_enrolled = c.id in enrolled_ids
        c.is_owner = request.user.is_authenticated and c.student_id == request.user.id
        course_info.append(c)

    if request.user.is_authenticated:
        profile, created = ProfileImg.objects.get_or_create(user=request.user)
        profile_img = profile
    else:
        profile_img = None

    context = {
        'course_info': course_info,
        'profile_img': profile_img,
    }
    return render(request, 'index.html', context)


def user_logout(request):
    logout(request)
    return redirect('index')


def priview(request, id):
    data = get_object_or_404(Course, id=id)

    is_owner = request.user.is_authenticated and data.student_id == request.user.id
    if not data.is_published and not (is_owner or request.user.is_staff):
        messages.error(request, 'This course is not published yet.')
        return redirect('index')

    return render(request, 'priview.html', {'data': data})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = None

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, email=user_obj.email, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)

            if user.role == 'teacher':
                return redirect('index')
            else:
                return redirect('index')

        else:
            messages.error(request, "Email or password is incorrect")

    return render(request, 'login.html')


# ============================================================
# FORGOT PASSWORD — EMAIL OTP
# ============================================================

SESSION_OTP_EMAIL   = 'otp_reset_email'
SESSION_OTP_VERIFIED = 'otp_reset_verified'


def _send_otp_email(user, code):
    subject = f'{settings.OTP_EMAIL_SUBJECT} {code}'
    body = (
        f'Hi {user.first_name or user.email},\n\n'
        f'Use this verification code to reset your password:\n\n'
        f'    {code}\n\n'
        f'The code expires in {PasswordResetOTP.OTP_TTL_MINUTES} minutes and can be used once.\n'
        f'If you did not ask to reset your password you can ignore this email.\n\n'
        f'— {settings.OTP_EMAIL_SENDER_NAME}'
    )
    try:
        send_mail(
            subject,
            body,
            settings.EMAIL_FROM_ADDRESS or None,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('index')

    email_in_session = request.session.get(SESSION_OTP_EMAIL)
    verified_email   = request.session.get(SESSION_OTP_VERIFIED)

    def back_to_start(**extra):
        request.session.pop(SESSION_OTP_EMAIL, None)
        request.session.pop(SESSION_OTP_VERIFIED, None)
        form = ForgotPasswordForm(initial={'email': request.POST.get('email') or None})
        ctx = {'form': form, 'step': 'request'}
        ctx.update(extra)
        return render(request, 'forgot_password.html', ctx)

    if request.method == 'GET':
        if verified_email:
            return render(request, 'forgot_password.html', {
                'step': 'password',
                'form': SetPasswordForm(),
                'email': verified_email,
            })
        if email_in_session:
            otp = _latest_otp(email_in_session)
            return render(request, 'forgot_password.html', _verify_context(
                request, email_in_session, OTPVerifyForm(),
            ))
        return render(request, 'forgot_password.html', {
            'step': 'request',
            'form': ForgotPasswordForm(),
        })

    step = request.POST.get('step', 'request')

    if step == 'request':
        form = ForgotPasswordForm(request.POST)
        if not form.is_valid():
            return render(request, 'forgot_password.html', {'form': form, 'step': 'request'})

        email = form.cleaned_data['email']
        user = User.objects.filter(email__iexact=email).first()

        wait = 0
        sent = True
        if user is not None:
            wait = _resend_wait(email)
            if wait <= 0:
                _, sent = _issue_otp(user)
                if sent:
                    request.session[SESSION_OTP_EMAIL] = user.email
                wait = _resend_wait(email)

        if not sent:
            return back_to_start(non_field_error=(
                'We could not send the email right now. Please try again in a moment.'
            ))

        return render(request, 'forgot_password.html', {
            'step': 'verify',
            'form': OTPVerifyForm(),
            'email': form.cleaned_data['email'],
            'seconds_left': PasswordResetOTP.OTP_TTL_MINUTES * 60,
            'resend_in': wait,
            'console_mode': settings.EMAIL_CONSOLE_MODE,
        })

    if step == 'verify':
        if not email_in_session:
            return back_to_start(non_field_error='Your session expired. Please request a new code.')

        form = OTPVerifyForm(request.POST)
        email = email_in_session
        otp = _latest_otp(email)

        if not form.is_valid():
            return _verify_page(request, email, form)

        if otp is None or not otp.is_usable:
            return _verify_page(request, email, form, otp_error=_otp_problem(otp))

        if not otp.check_code(form.cleaned_data['code']):
            otp.register_failed_attempt()
            if otp.attempts >= PasswordResetOTP.MAX_VERIFY_ATTEMPTS:
                return back_to_start(non_field_error='Too many wrong attempts. Please request a new code.')
            return _verify_page(request, email, form, otp_error='That code is not correct. Please try again.')

        request.session[SESSION_OTP_VERIFIED] = email
        request.session.pop(SESSION_OTP_EMAIL, None)
        return render(request, 'forgot_password.html', {
            'step': 'password',
            'form': SetPasswordForm(),
            'email': email,
        })

    if step == 'password':
        if not verified_email:
            return back_to_start(non_field_error='Your session expired. Please verify a new code.')

        form = SetPasswordForm(request.POST)
        if not form.is_valid():
            return render(request, 'forgot_password.html', {
                'step': 'password',
                'form': form,
                'email': verified_email,
            })

        user = User.objects.filter(email__iexact=verified_email).first()
        if user is None:
            return back_to_start(non_field_error='That account no longer exists.')

        otp = _latest_otp(verified_email)
        if otp is None or not otp.is_usable:
            return back_to_start(non_field_error='That code has expired. Please request a new one.')

        user.set_password(form.cleaned_data['new_password1'])
        user.save(update_fields=['password'])
        otp.consume()

        request.session.pop(SESSION_OTP_VERIFIED, None)
        request.session.pop(SESSION_OTP_EMAIL, None)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Your password has been reset. You are now signed in.')
        return redirect('index')

    return back_to_start()


def _latest_otp(email):
    return (
        PasswordResetOTP.objects
        .filter(user__email__iexact=email)
        .order_by('-created_at')
        .first()
    )


def _issue_otp(user):
    code = f'{secrets.randbelow(10 ** PasswordResetOTP.OTP_LENGTH):0{PasswordResetOTP.OTP_LENGTH}d}'

    if not _send_otp_email(user, code):
        return None, False

    PasswordResetOTP.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())

    otp = PasswordResetOTP(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=PasswordResetOTP.OTP_TTL_MINUTES),
    )
    otp.set_code(code)
    otp.save()

    return otp, True


def _resend_wait(email):
    otp = _latest_otp(email)
    if otp is None:
        return 0
    elapsed = (timezone.now() - otp.created_at).total_seconds()
    return max(0, int(PasswordResetOTP.RESEND_COOLDOWN_SECONDS - elapsed))


def _otp_problem(otp):
    if otp is None:
        return 'We could not find a code for this email. Please request a new one.'
    if otp.is_used:
        return 'That code has already been used. Please request a new one.'
    if otp.is_expired:
        return 'That code has expired. Please request a new one.'
    return 'Too many wrong attempts. Please request a new code.'


def _verify_context(request, email, form, otp_error=''):
    otp = _latest_otp(email)
    return {
        'step': 'verify',
        'form': form,
        'email': email,
        'otp_error': otp_error,
        'seconds_left': otp.seconds_left() if otp else 0,
        'resend_in': _resend_wait(email),
        'console_mode': settings.EMAIL_CONSOLE_MODE,
    }


def _verify_page(request, email, form, otp_error=''):
    return render(request, 'forgot_password.html', _verify_context(request, email, form, otp_error))


@login_required
def prof_course(request):
    if request.user.role != 'teacher':
        messages.error(request, "Only teachers can create or edit courses.")
        return redirect('user_profile')

    raw_id = request.POST.get('course_id') or request.GET.get('edit')
    course = None
    if raw_id:
        course = get_object_or_404(Course, id=raw_id, student=request.user)

    if request.method == 'POST':
        form = course_form(request.POST, request.FILES, instance=course)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.student = request.user
            if course is None:
                obj.is_published = False
            obj.save()
            if course is None:
                messages.success(
                    request,
                    f'Course "{obj.title}" saved as a draft. Click Publish to make it visible to students.'
                )
            else:
                messages.success(request, f'Course "{obj.title}" updated.')
            return redirect('user_profile')

        messages.error(request, 'Please fix the errors below and try again.')
        context = _profile_page_context(request, form=form, course_form_open=True)
        return render(request, 'user_profile.html', context)

    form = course_form(instance=course)
    context = _profile_page_context(request, form=form, course_form_open=bool(course))
    return render(request, 'user_profile.html', context)


@login_required
@require_POST
def publish_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, student=request.user)

    action = (request.POST.get('action') or 'publish').lower()
    if action in ('unpublish', 'draft'):
        course.is_published = False
        course.published_at = None
        message = 'Course moved back to draft. Students can no longer see it.'
    else:
        course.is_published = True
        course.published_at = course.published_at or timezone.now()
        message = 'Course published. Students can see it now.'

    course.save(update_fields=['is_published', 'published_at'])

    return JsonResponse({
        'success': True,
        'is_published': course.is_published,
        'message': message,
    })


def register_teacher(request):
    if request.method == 'POST':
        form = teacher_form(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = teacher_form()

    return render(request, 'teacher_add.html', {'form': form})


def setting(request):
    return render(request, 'setting.html')


@login_required
def quiz(request):
    course_id = request.GET.get('course_id')
    course = None
    quiz_obj = None

    if course_id:
        course = get_object_or_404(Course, id=course_id)

        quiz_obj = Quiz.objects.filter(
            course=course,
            teacher=request.user,
            is_published=False,
        ).first()

    context = {
        'course': course,
        'quiz': quiz_obj,
    }
    return render(request, 'quiz.html', context)


@login_required
@require_POST
def save_quiz(request):
    try:
        data = json.loads(request.body)

        course_id = data.get('course_id')
        if not course_id:
            return JsonResponse(
                {'status': 'error', 'message': 'No course selected.'},
                status=400
            )

        course = get_object_or_404(Course, id=course_id)

        quiz_obj = Quiz.objects.filter(
            course=course,
            teacher=request.user,
            is_published=False,
        ).first()

        if quiz_obj and quiz_obj.is_published:
            return JsonResponse(
                {'status': 'error', 'message': 'This quiz is published and cannot be edited.'},
                status=400
            )

        if quiz_obj is None:
            quiz_obj = Quiz.objects.create(
                course=course,
                teacher=request.user,
                title=data.get('title', 'Untitled Quiz'),
                is_published=False,
            )

        quiz_obj.title = data.get('title', quiz_obj.title)
        quiz_obj.description = data.get('description', '')
        quiz_obj.subject = data.get('subject', '')
        quiz_obj.chapter = data.get('chapter', '')
        quiz_obj.difficulty = data.get('difficulty', 'medium')
        quiz_obj.duration = int(data.get('duration', 30))
        quiz_obj.passing_score = int(data.get('passing_score', 70))
        quiz_obj.attempts_allowed = data.get('attempts_allowed', '2')
        quiz_obj.save()

        quiz_obj.questions.all().delete()

        for i, q in enumerate(data.get('questions', [])):
            q_type = q.get('type', 'mc')
            question = Question.objects.create(
                quiz=quiz_obj,
                question_type=q_type,
                text=q.get('text', ''),
                points=q.get('points', 2 if q_type == 'mc' else 5),
                order=i,
            )

            if q_type == 'mc':
                for j, ans in enumerate(q.get('answers', [])):
                    Answer.objects.create(
                        question=question,
                        text=ans.get('text', ''),
                        is_correct=ans.get('is_correct', False),
                        order=j,
                    )

        return JsonResponse({
            'status': 'success',
            'quiz_id': quiz_obj.id,
            'message': 'Quiz saved as draft!',
        })

    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )


@login_required
@require_POST
def delet_course(request, id):
    course_ = get_object_or_404(Course, id=id, student=request.user)
    title = course_.title
    course_.delete()
    messages.success(request, f'Course "{title}" deleted.')
    return redirect('user_profile')


@login_required
def user_profile(request):
    context = _profile_page_context(request)
    return render(request, 'user_profile.html', context)


def _teacher_courses(user):
    return (
        Course.objects
        .filter(student=user)
        .annotate(
            video_count=Count('playlists', distinct=True),
            lesson_count=Count('lessons', distinct=True),
            student_count=Count('enrollment', distinct=True),
            quiz_count=Count('quizzes', distinct=True),
        )
        .order_by('-id')
    )


def _enrolled_courses(user):
    return (
        Course.objects
        .filter(enrollment__student=user)
        .select_related('student')
        .annotate(
            video_count=Count('playlists', distinct=True),
            lesson_count=Count('lessons', distinct=True),
            quiz_count=Count('quizzes', distinct=True),
            student_count=Count('enrollment', distinct=True),
        )
        .distinct()
        .order_by('-id')
    )


def _profile_page_context(request, **extra):
    user = request.user
    profile, _ = ProfileImg.objects.get_or_create(user=user)

    my_courses = _teacher_courses(user)
    enrolled_courses = _enrolled_courses(user)

    first_owned_course = my_courses.first() if user.role == 'teacher' else None

    teacher_application = (
        TeacherApplication.objects
        .filter(user=user)
        .order_by('-id')
        .first()
    )

    if user.role == 'teacher':
        stats = {
            'courses': my_courses.count(),
            'published': my_courses.filter(is_published=True).count(),
            'drafts': my_courses.filter(is_published=False).count(),
            'videos': Playlist.objects.filter(course__student=user).count(),
            'students': Enrollment.objects.filter(course__student=user).count(),
        }
    else:
        stats = {
            'courses': enrolled_courses.count(),
            'published': enrolled_courses.count(),
            'drafts': 0,
            'videos': Playlist.objects.filter(
                course__enrollment__student=user,
                course__is_published=True,
            ).distinct().count(),
            'students': 0,
        }

    course_form_obj = extra.pop('form', None) or course_form()

    context = {
        'course_form': course_form_obj,
        'form': course_form_obj,
        'teacher_form': TeacherApplicationForm(),

        'data': my_courses,
        'enrolled_courses': enrolled_courses,

        'is_teacher': user.role == 'teacher',
        'teacher_application': teacher_application,
        'stats': stats,

        'student': user,
        'info': user,
        'profile': profile,
        'profileimgForm': ProfileImgForm(instance=profile),
        'playlist_max_upload_bytes': int(getattr(settings, 'PLAYLIST_MAX_UPLOAD_MB', 1024)) * 1024 * 1024,
        'first_owned_course': first_owned_course,
    }
    context.update(extra)
    return context


@login_required
def apply_teacher(request):
    if request.user.role == 'teacher':
        messages.info(request, "You are already a teacher.")
        return redirect('user_profile')

    if request.method == 'POST':
        existing = TeacherApplication.objects.filter(
            user=request.user,
            status__in=['pending', 'approved']
        ).first()

        if existing:
            if existing.status == 'pending':
                messages.warning(request, "You already have a pending application.")
            else:
                messages.info(request, "You are already an approved teacher.")
            return redirect('user_profile')

        form = TeacherApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = 'pending'
            application.save()
            messages.success(request, "Your application was submitted!")
            return redirect('user_profile')

        messages.error(request, 'Please fix the errors in your application.')
        context = _profile_page_context(
            request, teacher_form=form, teacher_form_open=True
        )
        return render(request, 'user_profile.html', context)

    context = _profile_page_context(request, teacher_form_open=True)
    return render(request, 'user_profile.html', context)


@login_required
def course_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()

    is_course_owner = (
        request.user.role == 'teacher'
        and course.student == request.user
    )

    if not enrollment and not is_course_owner:
        messages.error(request, "You don't have access to this course.")
        return redirect('user_profile')

    lessons = Lesson.objects.filter(
        course=course
    ).order_by('order', 'created_at')

    context = {
        'course': course,
        'lessons': lessons,
        'enrollment': enrollment,
        'total_lessons': lessons.count(),
        'is_teacher': request.user.role == 'teacher',
        'is_course_owner': is_course_owner,
    }

    return render(request, 'course_lessons.html', context)


@login_required
@require_POST
def profile_img_view(request):
    profile, _ = ProfileImg.objects.get_or_create(user=request.user)

    form = ProfileImgForm(request.POST, request.FILES, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile picture updated.')
    else:
        messages.error(
            request,
            'That image could not be uploaded. Use a JPG, PNG, GIF or WEBP file.'
        )

    return redirect('user_profile')


@login_required
def enroll_course(request, course_id):
    if request.method != "POST":
        return redirect("index")

    course = get_object_or_404(Course, id=course_id)

    if course.student == request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'error': 'You are the owner of this course.'
            }, status=400)

        messages.error(request, "You are the owner of this course.")
        return redirect("index")

    if not course.is_published and not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'error': 'This course is not published yet.'
            }, status=400)

        messages.error(request, "This course is not published yet.")
        return redirect("index")

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'created': created,
            'message': (
                'You have successfully enrolled in this course.'
                if created else
                'You are already enrolled in this course.'
            )
        })

    if created:
        messages.success(request, "You have successfully enrolled in this course.")
    else:
        messages.info(request, "You are already enrolled in this course.")

    return redirect("user_profile")


@login_required
def get_playlist_videos(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id)

        is_owner = (course.student == request.user)
        is_enrolled = Enrollment.objects.filter(
            student=request.user, course=course
        ).exists()

        if not (is_owner or is_enrolled or request.user.is_staff):
            return JsonResponse({
                'error': "You don't have access to this course playlist.",
                'videos': [],
                'quizzes': [],
            }, status=403)

        playlists = Playlist.objects.filter(course=course).order_by('created_at')

        videos = []
        for playlist in playlists:
            video_url  = playlist.video.url if playlist.video else ''
            video_name = (
                os.path.basename(playlist.video.name)
                if playlist.video else f'Video {playlist.id}'
            )
            videos.append({
                'id': playlist.id,
                'title': video_name,
                'video_url': video_url,
            })

        quizzes_qs = Quiz.objects.filter(course=course)
        if not is_owner:
            quizzes_qs = quizzes_qs.filter(is_published=True)
        quizzes_qs = quizzes_qs.order_by('-created_at')

        quizzes = []
        for q in quizzes_qs:
            if is_owner:
                quiz_url = reverse('quiz_submissions', args=[q.id])
                quiz_mode = 'submissions'
            elif q.is_published:
                quiz_url = reverse('take_quiz', args=[q.id])
                quiz_mode = 'take'
            else:
                quiz_url = ''
                quiz_mode = 'locked'

            quizzes.append({
                'id': q.id,
                'title': q.title,
                'description': q.description or '',
                'difficulty': q.difficulty,
                'duration': q.duration,
                'passing_score': q.passing_score,
                'total_questions': q.total_questions,
                'total_points': q.total_points,
                'quiz_url': quiz_url,
                'quiz_mode': quiz_mode,
                'is_published': q.is_published,
            })

        return JsonResponse({
            'course_id': course.id,
            'course_title': course.title,
            'is_owner': is_owner,
            'can_upload': is_owner,
            'owner_name': (
                f'{course.student.first_name} {course.student.last_name}'.strip()
                or course.student.email
            ),
            'is_published': course.is_published,
            'videos': videos,
            'quizzes': quizzes,
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'videos': [],
            'quizzes': [],
        }, status=500)


@login_required
@require_POST
def publish_quiz(request, quiz_id):
    try:
        quiz_obj = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

        if quiz_obj.is_published:
            return JsonResponse({
                'status': 'error',
                'message': 'Quiz is already published.',
            }, status=400)

        if quiz_obj.questions.count() == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot publish a quiz with no questions.',
            }, status=400)

        quiz_obj.is_published = True
        quiz_obj.published_at = timezone.now()
        quiz_obj.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Quiz published successfully!',
        })

    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )


@login_required
@require_POST
def add_playlist(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        return JsonResponse({
            'success': False,
            'error': 'Course not found.'
        }, status=404)

    if course.student != request.user:
        return JsonResponse({
            'success': False,
            'error': 'You can only add videos to your own courses.'
        }, status=403)

    try:
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({
                'success': False,
                'error': 'No video file provided'
            }, status=400)

        ALLOWED_VIDEO_EXT = (
            '.mp4', '.webm', '.ogv', '.ogg', '.mov', '.mkv',
            '.avi', '.wmv', '.flv', '.m4v', '.mpg', '.mpeg', '.3gp',
        )
        name = (video_file.name or '').lower()
        ext_ok = name.endswith(ALLOWED_VIDEO_EXT)
        mime_ok = (video_file.content_type or '').startswith('video/')
        if not (ext_ok or mime_ok):
            return JsonResponse({
                'success': False,
                'error': 'Unsupported video format. Allowed: ' + ', '.join(ALLOWED_VIDEO_EXT)
            }, status=400)

        playlist = Playlist.objects.create(
            course=course,
            video=video_file
        )

        video_name = os.path.basename(video_file.name)

        return JsonResponse({
            'success': True,
            'message': f'Video "{video_name}" added successfully!',
            'video': {
                'id': playlist.id,
                'title': video_name,
                'video_url': playlist.video.url
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def add_comment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    text = request.POST.get('text', '').strip()

    if not text:
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
        except:
            pass

    if not text:
        return JsonResponse({'status': 'error', 'error': 'Comment is empty'}, status=400)

    comment = Comment.objects.create(
        course=course,
        user=request.user,
        text=text
    )

    return JsonResponse({
        'status': 'success',
        'comment_id': comment.id,
        'author': comment.user.get_full_name() or comment.user.email,
        'text': comment.text,
        'created_at': comment.created_at.strftime('%H:%M'),
    })


@login_required
@require_POST
def remove_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'error': 'Not allowed'}, status=403)
    comment.delete()
    return JsonResponse({'status': 'removed'})


@login_required
@require_POST
def like_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    like, created = Like.objects.get_or_create(course=course, user=request.user)
    if not created:
        like.delete()
        return JsonResponse({'status': 'unliked', 'likes': course.likes.count()})
    return JsonResponse({'status': 'liked', 'likes': course.likes.count()})


@login_required
def get_like_status(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_liked = Like.objects.filter(course=course, user=request.user).exists()
    return JsonResponse({'is_liked': is_liked})


@login_required
def take_quiz(request, quiz_id):
    quiz_obj = get_object_or_404(Quiz, id=quiz_id)
    course   = quiz_obj.course

    is_quiz_author  = (quiz_obj.teacher == request.user)
    is_course_owner = (course.student == request.user)

    if is_quiz_author or is_course_owner:
        messages.error(
            request,
            "You can't take a quiz on a course you own. "
            "This quiz is for enrolled students only."
        )
        return redirect('user_profile')

    if not quiz_obj.is_published and not request.user.is_staff:
        messages.error(request, "This quiz is not published yet.")
        return redirect('index')

    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).first()

    if not enrollment:
        messages.error(request, "You don't have access to this quiz.")
        return redirect('index')

    try:
        profile_img = ProfileImg.objects.get(user=request.user)
    except ProfileImg.DoesNotExist:
        profile_img = None

    context = {
        'quiz': quiz_obj,
        'course': course,
        'profile_img': profile_img,
    }
    return render(request, 'take_quiz.html', context)


@login_required
@require_POST
def submit_quiz(request):
    try:
        data    = json.loads(request.body)
        quiz_id = data.get('quiz_id')
        answers = data.get('answers', [])

        if not quiz_id:
            return JsonResponse(
                {'status': 'error', 'message': 'Missing quiz_id.'},
                status=400
            )

        quiz_obj = get_object_or_404(Quiz, id=quiz_id)
        course   = quiz_obj.course

        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return JsonResponse(
                {'status': 'error', 'message': "You're not enrolled in this course."},
                status=403
            )

        if quiz_obj.teacher == request.user or course.student == request.user:
            return JsonResponse(
                {'status': 'error', 'message': "Owners can't submit this quiz."},
                status=403
            )

        if not quiz_obj.is_published:
            return JsonResponse(
                {'status': 'error', 'message': 'Quiz is not published.'},
                status=400
            )

        if quiz_obj.attempts_allowed != 'Unlimited':
            try:
                allowed = int(quiz_obj.attempts_allowed)
            except (TypeError, ValueError):
                allowed = None
            if allowed:
                used = QuizAttempt.objects.filter(
                    quiz=quiz_obj,
                    student=request.user,
                ).exclude(status='in_progress').count()
                if used >= allowed:
                    return JsonResponse(
                        {
                            'status': 'error',
                            'message': (
                                f'You have already used all {allowed} allowed '
                                f'attempt(s) for this quiz.'
                            ),
                        },
                        status=403,
                    )

        attempt = QuizAttempt.objects.create(
            quiz=quiz_obj,
            student=request.user,
            status='submitted',
            submitted_at=timezone.now(),
        )

        answer_map = {a['question_id']: a for a in answers}

        total_auto_score    = 0
        has_manual_question = False

        for question in quiz_obj.questions.all():
            sub = answer_map.get(question.id, {})

            if question.question_type == 'mc':
                selected_id = sub.get('answer_id')
                selected    = None
                is_correct  = False

                if selected_id:
                    try:
                        selected = Answer.objects.get(
                            id=selected_id,
                            question=question,
                        )
                        is_correct = selected.is_correct
                    except Answer.DoesNotExist:
                        selected = None

                points = question.points if is_correct else 0
                total_auto_score += points

                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected=selected,
                    is_correct=is_correct,
                    points_awarded=points,
                    graded_at=timezone.now(),
                )

            else:
                has_manual_question = True

                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=sub.get('text', ''),
                    is_correct=False,
                    points_awarded=0,
                )

        attempt.score = total_auto_score
        if not has_manual_question:
            attempt.status    = 'graded'
            attempt.graded_at = timezone.now()
        attempt.save()

        return JsonResponse({
            'status':        'success',
            'message':       'Quiz submitted successfully!',
            'attempt_id':    attempt.id,
            'score':         attempt.total_score,
            'percentage':    attempt.percentage,
            'needs_grading': has_manual_question,
            'redirect_url':  reverse('quiz_result', kwargs={'attempt_id': attempt.id}),
        })

    except Quiz.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': 'Quiz not found.'},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )


@login_required
def quiz_submissions(request, quiz_id):
    quiz_obj = get_object_or_404(Quiz, id=quiz_id)

    if quiz_obj.teacher != request.user and quiz_obj.course.student != request.user:
        messages.error(request, "You don't have access to this quiz's submissions.")
        return redirect('user_profile')

    attempts = (
        QuizAttempt.objects
        .filter(quiz=quiz_obj)
        .select_related('student')
        .order_by('-submitted_at')
    )

    total     = attempts.count()
    submitted = attempts.filter(status='submitted').count()
    graded    = attempts.filter(status='graded').count()
    passed    = sum(1 for a in attempts if a.status == 'graded' and a.passed)

    context = {
        'quiz':     quiz_obj,
        'course':   quiz_obj.course,
        'attempts': attempts,
        'stats': {
            'total':     total,
            'submitted': submitted,
            'graded':    graded,
            'passed':    passed,
        },
    }
    return render(request, 'quiz_submission.html', context)


@login_required
def attempt_detail(request, attempt_id):
    attempt  = get_object_or_404(QuizAttempt, id=attempt_id)
    quiz_obj = attempt.quiz

    if quiz_obj.teacher != request.user and quiz_obj.course.student != request.user:
        messages.error(request, "You don't have access to this attempt.")
        return redirect('user_profile')

    answers = (
        attempt.answers
        .select_related('question', 'selected')
        .order_by('question__order')
    )

    context = {
        'attempt': attempt,
        'quiz':    quiz_obj,
        'course':  quiz_obj.course,
        'answers': answers,
    }
    return render(request, 'attempt_details.html', context)


@login_required
@require_POST
def grade_attempt(request, attempt_id):
    attempt  = get_object_or_404(QuizAttempt, id=attempt_id)
    quiz_obj = attempt.quiz

    if quiz_obj.teacher != request.user and quiz_obj.course.student != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not allowed.'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)

    for g in data.get('grades', []):
        try:
            ans = StudentAnswer.objects.get(id=g['answer_id'], attempt=attempt)
        except StudentAnswer.DoesNotExist:
            continue

        pts = max(0, min(float(g.get('points', 0)), ans.question.points))
        ans.points_awarded   = pts
        ans.teacher_feedback = g.get('feedback', '')
        ans.is_correct       = (pts >= ans.question.points)
        ans.graded_at        = timezone.now()
        ans.save()

    attempt.manual_score = sum(
        a.points_awarded
        for a in attempt.answers.filter(question__question_type='explain')
    )
    attempt.status    = 'graded'
    attempt.graded_by = request.user
    attempt.graded_at = timezone.now()
    attempt.save()

    return JsonResponse({
        'status':      'success',
        'message':     'Grades saved.',
        'total_score': attempt.total_score,
        'percentage':  attempt.percentage,
    })


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    is_owner   = (attempt.student == request.user)
    is_teacher = (
        attempt.quiz.teacher == request.user
        or attempt.quiz.course.student == request.user
    )

    if not (is_owner or is_teacher):
        messages.error(request, "You don't have access to this result.")
        return redirect('index')

    answers = (
        attempt.answers
        .select_related('question', 'selected')
        .order_by('question__order')
    )

    context = {
        'attempt':         attempt,
        'quiz':            attempt.quiz,
        'answers':         answers,
        'is_teacher_view': is_teacher and not is_owner,
    }
    return render(request, 'quiz_result.html', context)


# ============================================================
# AI STUDY ASSISTANT — DeepSeek (students and teachers can ask)
# ============================================================

AI_SYSTEM_PROMPT = (
    "You are the AI Study Assistant for the Online Study platform, used by both "
    "students and teachers. Help with course topics, explain concepts simply, "
    "summarize lessons, help teachers draft quiz questions, and suggest study "
    "plans. Answer in clear, friendly language and keep replies focused. If "
    "asked about something unrelated to studying or teaching, say politely that "
    "you focus on learning topics and offer to help with one. Never do "
    "homework-exam cheating - guide instead."
)


def _call_deepseek(messages):
    """Call the DeepSeek chat completions API. Returns the reply text.

    DeepSeek uses an OpenAI-compatible format. urllib keeps this dependency-free.
    `messages` is an alternating list of {role: 'user'|'assistant', content}.
    """
    import json as _json
    import urllib.request

    api_messages = [{'role': 'system', 'content': AI_SYSTEM_PROMPT}]
    for m in messages:
        role = 'assistant' if m['role'] == 'assistant' else 'user'
        api_messages.append({'role': role, 'content': m['content']})

    payload = _json.dumps({
        'model': settings.DEEPSEEK_MODEL,
        'messages': api_messages,
        'temperature': 0.7,
        'max_tokens': 1024,
        'stream': False,
    }).encode('utf-8')

    request = urllib.request.Request(
        f'{settings.DEEPSEEK_BASE_URL}/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
        },
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=settings.DEEPSEEK_TIMEOUT) as response:
        data = _json.loads(response.read().decode('utf-8'))

    try:
        return data['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError('Unexpected DeepSeek API response shape.')


@login_required
def ai_assistant(request):
    """Chat page. Shows the user's conversation history and, while no DeepSeek
    API key is configured, explains how to enable the assistant."""
    history = request.user.ai_chat_messages.all()
    if request.user.role == 'teacher':
        my_courses = Course.objects.filter(student=request.user)
    else:
        my_courses = Course.objects.filter(enrollment__student=request.user)
    return render(request, 'ai_assistant.html', {
        'history': history,
        'ai_enabled': bool(settings.DEEPSEEK_API_KEY),
        'my_courses': my_courses.order_by('title')[:20],
    })


def _ai_course_context(user):
    """Short per-user context line the assistant receives with each question."""
    if user.role == 'teacher':
        titles = list(
            Course.objects.filter(student=user)
            .order_by('-published_at', 'title')
            .values_list('title', flat=True)[:5]
        )
        if titles:
            return f"The user is a teacher. Their courses on the platform: {', '.join(titles)}."
        return 'The user is a teacher with no courses yet on the platform.'
    titles = list(
        Course.objects.filter(enrollment__student=user)
        .order_by('title').values_list('title', flat=True)[:5]
    )
    if titles:
        return f"The user is a student. Courses they are enrolled in: {', '.join(titles)}."
    return 'The user is a student not enrolled in any course yet.'


@login_required
@require_POST
def ask_ai(request):
    """Receive {question, course_id?}, answer via DeepSeek, store both sides."""
    if not settings.DEEPSEEK_API_KEY:
        return JsonResponse({
            'success': False,
            'error': 'AI is not configured yet. Add DEEPSEEK_API_KEY and restart the server.',
            'code': 'not_configured',
        }, status=503)

    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        data = request.POST

    question = (data.get('question') or '').strip()
    if not question:
        return JsonResponse({'success': False, 'error': 'Please type a question.'}, status=400)
    if len(question) > 2000:
        return JsonResponse(
            {'success': False, 'error': 'Questions are limited to 2000 characters.'},
            status=400,
        )

    course = None
    course_id = data.get('course_id')
    if course_id:
        course = Course.objects.filter(id=course_id).first()

    prior = list(
        request.user.ai_chat_messages.order_by('-created_at')
        .values('role', 'content')[: settings.AI_HISTORY_TURNS * 2]
    )
    prior.reverse()

    api_messages = [{'role': 'user', 'content': _ai_course_context(request.user)}]
    if course is not None:
        api_messages.append({
            'role': 'assistant',
            'content': f'Understood. Your question is about the course "{course.title}".',
        })
    api_messages += prior + [{'role': 'user', 'content': question}]

    try:
        reply = _call_deepseek(api_messages)
    except Exception as exc:
        return JsonResponse({
            'success': False,
            'error': 'The AI service is unavailable right now. Please try again shortly.',
            'detail': f'{type(exc).__name__}: {exc}' if settings.DEBUG else '',
        }, status=502)

    AIChatMessage.objects.bulk_create([
        AIChatMessage(user=request.user, role='user', content=question),
        AIChatMessage(user=request.user, role='assistant', content=reply),
    ])
    return JsonResponse({
        'success': True,
        'reply': reply,
        'question': question,
    })


@login_required
@require_POST
def clear_ai_chat(request):
    """Delete the user's whole conversation."""
    deleted, _ = request.user.ai_chat_messages.all().delete()
    return JsonResponse({'success': True, 'deleted': deleted})


# ============================================================
# ADMIN — PLATFORM DATA ANALYSIS REPORT
# ============================================================

def _growth_pct(current, previous):
    """Signed percentage change, tolerant of a zero baseline."""
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _build_analytics():
    """Compute the whole platform report as a plain dict. Shared by the
    HTML page and the CSV export so the two can never disagree."""
    now = timezone.now()
    today = now.date()

    overview = {
        'users': User.objects.count(),
        'students': User.objects.filter(role='student').count(),
        'teachers': User.objects.filter(role='teacher').count(),
        'courses': Course.objects.count(),
        'published_courses': Course.objects.filter(is_published=True).count(),
        'draft_courses': Course.objects.filter(is_published=False).count(),
        'enrollments': Enrollment.objects.count(),
        'videos': Playlist.objects.count(),
        'quizzes': Quiz.objects.count(),
        'published_quizzes': Quiz.objects.filter(is_published=True).count(),
        'quiz_attempts': QuizAttempt.objects.count(),
        'submitted_attempts': QuizAttempt.objects.filter(
            status__in=['submitted', 'graded']).count(),
        'comments': Comment.objects.count(),
        'likes': Like.objects.count(),
        'posts': Post.objects.count(),
        'pending_applications': TeacherApplication.objects.filter(status='pending').count(),
        'approved_applications': TeacherApplication.objects.filter(status='approved').count(),
        'rejected_applications': TeacherApplication.objects.filter(status='rejected').count(),
        'password_resets': PasswordResetOTP.objects.count(),
        'ai_messages': AIChatMessage.objects.count(),
    }
    overview['avg_courses_per_teacher'] = (
        round(overview['courses'] / overview['teachers'], 1)
        if overview['teachers'] else 0
    )
    overview['avg_enrollments_per_student'] = (
        round(overview['enrollments'] / overview['students'], 1)
        if overview['students'] else 0
    )

    daily = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        daily.append({
            'date': day.strftime('%b %d'),
            'users': User.objects.filter(date_joined__date=day).count(),
            'enrollments': Enrollment.objects.filter(enrolled_at__date=day).count(),
            'attempts': QuizAttempt.objects.filter(started_at__date=day).count(),
            'comments': Comment.objects.filter(created_at__date=day).count(),
        })

    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)
    growth = {
        'users': _growth_pct(
            User.objects.filter(date_joined__date__gte=week_start).count(),
            User.objects.filter(
                date_joined__date__gte=prev_start,
                date_joined__date__lt=week_start,
            ).count(),
        ),
        'enrollments': _growth_pct(
            Enrollment.objects.filter(enrolled_at__date__gte=week_start).count(),
            Enrollment.objects.filter(
                enrolled_at__date__gte=prev_start,
                enrolled_at__date__lt=week_start,
            ).count(),
        ),
    }

    cat_counts = {
        row['category']: row['c']
        for row in Course.objects.values('category').annotate(c=Count('id'))
    }
    courses_by_category = sorted(
        (
            {'label': label, 'count': cat_counts.get(code, 0)}
            for code, label in Course.COURSE_CATEGORY
        ),
        key=lambda row: -row['count'],
    )
    level_counts = {
        row['level']: row['c']
        for row in Course.objects.values('level').annotate(c=Count('id'))
    }
    courses_by_level = [
        {'label': label, 'count': level_counts.get(code, 0)}
        for code, label in Course.COURSE_LEVEL
    ]

    top_courses = (
        Course.objects
        .select_related('student')
        .annotate(
            enrollments_count=Count('enrollment', distinct=True),
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            videos_count=Count('playlists', distinct=True),
        )
        .order_by('-enrollments_count', '-likes_count', '-comments_count')[:10]
    )

    top_teachers = (
        User.objects
        .filter(role='teacher')
        .annotate(
            courses_count=Count('course', distinct=True),
            enrollments_received=Count('course__enrollment', distinct=True),
            likes_received=Count('course__likes', distinct=True),
        )
        .order_by('-enrollments_received', '-courses_count')[:10]
    )

    top_students = (
        User.objects
        .filter(role='student')
        .annotate(
            enrollments_count=Count('enrollment', distinct=True),
            attempts_count=Count('quiz_attempts', distinct=True),
            comments_count=Count('comment', distinct=True),
        )
        .order_by('-enrollments_count', '-attempts_count')[:10]
    )

    quiz_rows = []
    quizzes = Quiz.objects.select_related('course', 'teacher').annotate(
        attempts_total=Count('attempts', distinct=True),
    )
    for quiz in quizzes:
        finished = list(quiz.attempts.filter(status__in=['submitted', 'graded']))
        quiz_rows.append({
            'quiz': quiz,
            'course': quiz.course,
            'teacher': quiz.teacher,
            'attempts_total': quiz.attempts_total,
            'finished': len(finished),
            'passed': sum(1 for a in finished if a.passed),
            'avg_pct': (
                round(sum(a.percentage for a in finished) / len(finished), 1)
                if finished else None
            ),
        })
    quiz_rows.sort(key=lambda row: (-row['attempts_total'], row['quiz'].title))

    submitted_total = sum(row['finished'] for row in quiz_rows)
    passed_total = sum(row['passed'] for row in quiz_rows)
    avg_pct_overall = None
    if submitted_total:
        pct_sum, pct_count = 0, 0
        for attempt in QuizAttempt.objects.filter(
            status__in=['submitted', 'graded']
        ).select_related('quiz'):
            pct_sum += attempt.percentage
            pct_count += 1
        avg_pct_overall = round(pct_sum / pct_count, 1) if pct_count else None

    quiz_summary = {
        'submitted': submitted_total,
        'passed': passed_total,
        'failed': submitted_total - passed_total,
        'pass_rate': (
            round(passed_total / submitted_total * 100, 1)
            if submitted_total else 0
        ),
        'avg_pct': avg_pct_overall,
    }

    recent_enrollments = (
        Enrollment.objects
        .select_related('student', 'course')
        .order_by('-enrolled_at')[:12]
    )
    recent_attempts = (
        QuizAttempt.objects
        .filter(status__in=['submitted', 'graded'])
        .select_related('student', 'quiz', 'quiz__course')
        .order_by('-submitted_at', '-started_at')[:12]
    )
    recent_comments = (
        Comment.objects
        .select_related('user', 'course')
        .order_by('-created_at')[:8]
    )

    courses_max = max(
        [row['count'] for row in courses_by_category]
        + [row['count'] for row in courses_by_level] + [1]
    )

    return {
        'generated_at': now,
        'overview': overview,
        'growth': growth,
        'daily': daily,
        'courses_by_category': courses_by_category,
        'courses_by_level': courses_by_level,
        'courses_max': courses_max,
        'top_courses': top_courses,
        'top_teachers': top_teachers,
        'top_students': top_students,
        'quiz_rows': quiz_rows,
        'quiz_summary': quiz_summary,
        'recent_enrollments': recent_enrollments,
        'recent_attempts': recent_attempts,
        'recent_comments': recent_comments,
    }


@login_required
def admin_analytics(request):
    """Superuser-only data analysis report covering every model."""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to view the analytics report.")
        return redirect('index')
    return render(request, 'admin_analytics.html', _build_analytics())


@login_required
def admin_analytics_csv(request):
    """Download the same report as a CSV file."""
    if not request.user.is_superuser:
        return HttpResponseForbidden('Admins only.')

    report = _build_analytics()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="onlinestudy-report-{timezone.now():%Y-%m-%d}.csv"'
    )
    writer = csv.writer(response)

    writer.writerow(['Online Study - Platform Data Analysis Report'])
    writer.writerow(['Generated', report['generated_at'].strftime('%Y-%m-%d %H:%M')])
    writer.writerow([])

    writer.writerow(['OVERVIEW'])
    for key, value in report['overview'].items():
        writer.writerow([key.replace('_', ' ').title(), value])
    writer.writerow([])

    writer.writerow(['DAILY ACTIVITY (LAST 14 DAYS)'])
    writer.writerow(['Date', 'New Users', 'New Enrollments', 'Quiz Attempts', 'Comments'])
    for row in report['daily']:
        writer.writerow([row['date'], row['users'], row['enrollments'], row['attempts'], row['comments']])
    writer.writerow([])

    writer.writerow(['COURSES BY CATEGORY'])
    for row in report['courses_by_category']:
        if row['count']:
            writer.writerow([row['label'], row['count']])
    writer.writerow([])

    writer.writerow(['COURSES BY LEVEL'])
    for row in report['courses_by_level']:
        if row['count']:
            writer.writerow([row['label'], row['count']])
    writer.writerow([])

    writer.writerow(['TOP COURSES BY ENGAGEMENT'])
    writer.writerow(['Course', 'Teacher', 'Published', 'Enrollments', 'Likes', 'Comments', 'Videos'])
    for c in report['top_courses']:
        writer.writerow([
            c.title, c.student.email, 'Yes' if c.is_published else 'No',
            c.enrollments_count, c.likes_count, c.comments_count, c.videos_count,
        ])
    writer.writerow([])

    writer.writerow(['TOP TEACHERS'])
    writer.writerow(['Teacher', 'Courses', 'Enrollments Received', 'Likes Received'])
    for t in report['top_teachers']:
        writer.writerow([t.email, t.courses_count, t.enrollments_received, t.likes_received])
    writer.writerow([])

    writer.writerow(['TOP STUDENTS'])
    writer.writerow(['Student', 'Enrollments', 'Quiz Attempts', 'Comments'])
    for s in report['top_students']:
        writer.writerow([s.email, s.enrollments_count, s.attempts_count, s.comments_count])
    writer.writerow([])

    writer.writerow(['QUIZ PERFORMANCE'])
    writer.writerow(['Quiz', 'Course', 'Teacher', 'Attempts', 'Submitted', 'Passed', 'Avg %'])
    for row in report['quiz_rows']:
        writer.writerow([
            row['quiz'].title,
            row['course'].title if row['course'] else '-',
            row['teacher'].email if row['teacher'] else '-',
            row['attempts_total'], row['finished'], row['passed'],
            row['avg_pct'] if row['avg_pct'] is not None else '-',
        ])
    writer.writerow([])

    summary = report['quiz_summary']
    writer.writerow(['QUIZ SUMMARY'])
    writer.writerow(['Submitted', summary['submitted']])
    writer.writerow(['Passed', summary['passed']])
    writer.writerow(['Failed', summary['failed']])
    writer.writerow(['Pass Rate %', summary['pass_rate']])
    writer.writerow(['Average Score %', summary['avg_pct'] if summary['avg_pct'] is not None else '-'])
    writer.writerow([])

    writer.writerow(['RECENT ENROLLMENTS'])
    writer.writerow(['Student', 'Course', 'Date'])
    for e in report['recent_enrollments']:
        writer.writerow([e.student.email, e.course.title, e.enrolled_at.strftime('%Y-%m-%d %H:%M')])

    return response


# ============================================================
# TEACHER — MY DATA ANALYSIS REPORT (scoped to one teacher)
# ============================================================

def _build_teacher_analytics(teacher):
    """Compute the teacher's own report as a plain dict, scoped strictly to
    the courses this teacher owns and the quizzes they created. Shared by
    the HTML page and the CSV export so the two can never disagree."""
    now = timezone.now()
    today = now.date()

    courses = Course.objects.filter(student=teacher)
    quizzes = Quiz.objects.filter(
        Q(teacher=teacher) | Q(course__student=teacher)
    ).distinct()
    course_ids = list(courses.values_list('id', flat=True))

    enrollments = Enrollment.objects.filter(course_id__in=course_ids)
    attempts = QuizAttempt.objects.filter(quiz__in=quizzes)
    submitted = attempts.filter(status__in=['submitted', 'graded'])

    submitted_count = submitted.count()
    passed_count = 0
    pct_sum = 0.0
    for attempt in submitted:          # passed/percentage are Python props
        if attempt.passed:
            passed_count += 1
        pct_sum += attempt.percentage

    overview = {
        'courses': courses.count(),
        'published_courses': courses.filter(is_published=True).count(),
        'draft_courses': courses.filter(is_published=False).count(),
        'enrollments': enrollments.count(),
        'unique_students': enrollments.values('student_id').distinct().count(),
        'videos': Playlist.objects.filter(course_id__in=course_ids).count(),
        'lessons': Lesson.objects.filter(course_id__in=course_ids).count(),
        'quizzes': quizzes.count(),
        'published_quizzes': quizzes.filter(is_published=True).count(),
        'quiz_attempts': attempts.count(),
        'submitted_attempts': submitted_count,
        'comments': Comment.objects.filter(course_id__in=course_ids).count(),
        'likes': Like.objects.filter(course_id__in=course_ids).count(),
    }
    overview['avg_enrollments_per_course'] = (
        round(overview['enrollments'] / overview['courses'], 1)
        if overview['courses'] else 0
    )
    overview['pass_rate'] = (
        round(passed_count / submitted_count * 100, 1)
        if submitted_count else 0
    )
    overview['avg_score'] = (
        round(pct_sum / submitted_count, 1) if submitted_count else None
    )

    # ---- daily activity, last 14 days (this teacher's data only) ----
    daily = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        daily.append({
            'date': day.strftime('%b %d'),
            'enrollments': enrollments.filter(enrolled_at__date=day).count(),
            'attempts': attempts.filter(started_at__date=day).count(),
            'comments': Comment.objects.filter(
                course_id__in=course_ids, created_at__date=day).count(),
        })

    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)
    growth = {
        'enrollments': _growth_pct(
            enrollments.filter(enrolled_at__date__gte=week_start).count(),
            enrollments.filter(
                enrolled_at__date__gte=prev_start,
                enrolled_at__date__lt=week_start,
            ).count(),
        ),
    }

    # ---- per-course table ----
    course_rows = list(
        courses.select_related('student').annotate(
            enrollments_count=Count('enrollment', distinct=True),
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            videos_count=Count('playlists', distinct=True),
            lessons_count=Count('lessons', distinct=True),
        ).order_by('-enrollments_count', '-likes_count', 'title')
    )
    courses_max = 1
    for row in course_rows:
        courses_max = max(
            courses_max, row.enrollments_count, row.likes_count,
            row.comments_count, row.videos_count,
        )

    # ---- per-quiz performance (percentage is a Python property) ----
    quiz_rows = []
    for quiz in quizzes.select_related('course').annotate(
        attempts_total=Count('attempts', distinct=True),
    ):
        finished = list(quiz.attempts.filter(status__in=['submitted', 'graded']))
        quiz_rows.append({
            'quiz': quiz,
            'course': quiz.course,
            'attempts_total': quiz.attempts_total,
            'finished': len(finished),
            'passed': sum(1 for a in finished if a.passed),
            'avg_pct': (
                round(sum(a.percentage for a in finished) / len(finished), 1)
                if finished else None
            ),
        })
    quiz_rows.sort(key=lambda row: (-row['attempts_total'], row['quiz'].title))

    # ---- most active students inside this teacher's courses ----
    top_students = list(
        User.objects
        .filter(role='student', enrollment__course_id__in=course_ids)
        .distinct()
        .annotate(
            enrollments_count=Count(
                'enrollment',
                filter=Q(enrollment__course_id__in=course_ids),
                distinct=True,
            ),
            attempts_count=Count(
                'quiz_attempts',
                filter=Q(quiz_attempts__quiz__in=quizzes),
                distinct=True,
            ),
            comments_count=Count(
                'comment',
                filter=Q(comment__course_id__in=course_ids),
                distinct=True,
            ),
        )
        .order_by('-enrollments_count', '-attempts_count', 'email')[:10]
    )

    recent_enrollments = (
        enrollments.select_related('student', 'course').order_by('-enrolled_at')[:12]
    )
    recent_attempts = (
        submitted.select_related('student', 'quiz', 'quiz__course')
        .order_by('-submitted_at', '-started_at')[:8]
    )
    recent_comments = (
        Comment.objects.filter(course_id__in=course_ids)
        .select_related('user', 'course')
        .order_by('-created_at')[:8]
    )

    return {
        'generated_at': now,
        'teacher': teacher,
        'overview': overview,
        'growth': growth,
        'daily': daily,
        'course_rows': course_rows,
        'courses_max': courses_max,
        'quiz_rows': quiz_rows,
        'quiz_summary': {
            'submitted': submitted_count,
            'passed': passed_count,
            'failed': submitted_count - passed_count,
            'pass_rate': overview['pass_rate'],
            'avg_pct': overview['avg_score'],
        },
        'top_students': top_students,
        'recent_enrollments': recent_enrollments,
        'recent_attempts': recent_attempts,
        'recent_comments': recent_comments,
    }


@login_required
def teacher_analytics(request):
    """The logged-in teacher's own data analysis report (superusers may
    preview their own too)."""
    if not (request.user.is_superuser or request.user.role == 'teacher'):
        messages.error(request, "You don't have permission to view the analytics report.")
        return redirect('index')
    return render(request, 'teacher_analytics.html', _build_teacher_analytics(request.user))


@login_required
def teacher_analytics_csv(request):
    """Download the teacher's own report as a CSV file."""
    if not (request.user.is_superuser or request.user.role == 'teacher'):
        return HttpResponseForbidden('Teachers only.')

    report = _build_teacher_analytics(request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="onlinestudy-teacher-report-{timezone.now():%Y-%m-%d}.csv"'
    )
    writer = csv.writer(response)

    writer.writerow(['Online Study - Teacher Data Analysis Report'])
    writer.writerow(['Teacher', report['teacher'].email])
    writer.writerow(['Generated', report['generated_at'].strftime('%Y-%m-%d %H:%M')])
    writer.writerow([])

    writer.writerow(['OVERVIEW'])
    for key, value in report['overview'].items():
        writer.writerow([key.replace('_', ' ').title(), value])
    writer.writerow([])

    writer.writerow(['DAILY ACTIVITY (LAST 14 DAYS)'])
    writer.writerow(['Date', 'New Enrollments', 'Quiz Attempts', 'Comments'])
    for row in report['daily']:
        writer.writerow([row['date'], row['enrollments'], row['attempts'], row['comments']])
    writer.writerow([])

    writer.writerow(['MY COURSES'])
    writer.writerow(['Course', 'Status', 'Price', 'Enrollments', 'Likes', 'Comments', 'Videos', 'Lessons'])
    for c in report['course_rows']:
        writer.writerow([
            c.title, 'Published' if c.is_published else 'Draft', c.Course_price,
            c.enrollments_count, c.likes_count, c.comments_count,
            c.videos_count, c.lessons_count,
        ])
    writer.writerow([])

    writer.writerow(['QUIZ PERFORMANCE'])
    writer.writerow(['Quiz', 'Course', 'Attempts', 'Submitted', 'Passed', 'Avg %'])
    for row in report['quiz_rows']:
        writer.writerow([
            row['quiz'].title,
            row['course'].title if row['course'] else '-',
            row['attempts_total'], row['finished'], row['passed'],
            row['avg_pct'] if row['avg_pct'] is not None else '-',
        ])
    writer.writerow([])

    summary = report['quiz_summary']
    writer.writerow(['QUIZ SUMMARY'])
    writer.writerow(['Submitted', summary['submitted']])
    writer.writerow(['Passed', summary['passed']])
    writer.writerow(['Failed', summary['failed']])
    writer.writerow(['Pass Rate %', summary['pass_rate']])
    writer.writerow(['Average Score %', summary['avg_pct'] if summary['avg_pct'] is not None else '-'])
    writer.writerow([])

    writer.writerow(['MOST ACTIVE STUDENTS'])
    writer.writerow(['Student', 'Enrollments', 'Quiz Attempts', 'Comments'])
    for s in report['top_students']:
        writer.writerow([s.email, s.enrollments_count, s.attempts_count, s.comments_count])
    writer.writerow([])

    writer.writerow(['RECENT ENROLLMENTS'])
    writer.writerow(['Student', 'Course', 'Date'])
    for e in report['recent_enrollments']:
        writer.writerow([e.student.email, e.course.title, e.enrolled_at.strftime('%Y-%m-%d %H:%M')])

    return response