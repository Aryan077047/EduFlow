from django.shortcuts import render, redirect, get_object_or_404
from .form import course_form, teacher_form, TeacherApplicationForm, ProfileImgForm, PlaylistForm
from .form import ForgotPasswordForm, OTPVerifyForm, SetPasswordForm
from django.conf import settings
from django.core.mail import send_mail
import secrets
from django.contrib.auth.decorators import login_required
from .models import Course, TeacherApplication, ProfileImg, Enrollment, Playlist, Lesson, Post, Comment, Like, Quiz, Question, Answer, QuizAttempt, StudentAnswer, PasswordResetOTP
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

    # Prefetch comments with their authors so the homepage does not run one
    # query per course (and another per comment) inside the loop below.
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
SESSION_OTP_DEV_CODE = 'otp_dev_code'


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
        request.session.pop(SESSION_OTP_DEV_CODE, None)
        form = ForgotPasswordForm(request.POST.get('email') or None)
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
        if user is not None:
            wait = _resend_wait(email)
            if wait <= 0:
                _issue_otp(request, user)
                request.session[SESSION_OTP_EMAIL] = user.email
                wait = _resend_wait(email)

        return render(request, 'forgot_password.html', {
            'step': 'verify',
            'form': OTPVerifyForm(),
            'email': form.cleaned_data['email'],
            'seconds_left': PasswordResetOTP.OTP_TTL_MINUTES * 60,
            'resend_in': wait,
            'console_mode': settings.EMAIL_CONSOLE_MODE,
            'dev_code': request.session.get(SESSION_OTP_DEV_CODE) if settings.EMAIL_CONSOLE_MODE else None,
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
        request.session.pop(SESSION_OTP_DEV_CODE, None)
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
        request.session.pop(SESSION_OTP_DEV_CODE, None)
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


def _issue_otp(request, user):
    PasswordResetOTP.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())

    code = f'{secrets.randbelow(10 ** PasswordResetOTP.OTP_LENGTH):0{PasswordResetOTP.OTP_LENGTH}d}'
    otp = PasswordResetOTP(
        user=user,
        expires_at=timezone.now() + timedelta(minutes=PasswordResetOTP.OTP_TTL_MINUTES),
    )
    otp.set_code(code)
    otp.save()
    _send_otp_email(user, code)

    if settings.EMAIL_CONSOLE_MODE:
        request.session[SESSION_OTP_DEV_CODE] = code
    else:
        request.session.pop(SESSION_OTP_DEV_CODE, None)

    return otp


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
        'dev_code': request.session.get(SESSION_OTP_DEV_CODE) if settings.EMAIL_CONSOLE_MODE else None,
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

        # Enforce the quiz's attempt limit ('1', '2', '3' or 'Unlimited').
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