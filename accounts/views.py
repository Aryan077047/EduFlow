import json
import secrets
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    teacher_form,
    ProfileImgForm,
    ForgotPasswordForm,
    OTPVerifyForm,
    SetPasswordForm,
    ChangePasswordForm,
    EditProfileForm,
)
from .models import AIChatMessage, PasswordResetOTP, ProfileImg
from teacher.forms import TeacherApplicationForm, course_form
from teacher.models import Course, Playlist, TeacherApplication
from student.models import Comment, Enrollment

User = get_user_model()


def index(request):

    # Superusers browse the home page like everyone else; they can reach the
    # admin dashboard via the shield button in the header instead.

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
            # A pre-login language choice (cookie) seeds the new session.
            from onlinestudy.i18n_local import LANGUAGES
            cookie_lang = request.COOKIES.get(settings.SITE_LANG_COOKIE)
            if cookie_lang in LANGUAGES and user.language != cookie_lang:
                user.language = cookie_lang
                user.save(update_fields=['language'])
            login(request, user)

            if user.role == 'teacher':
                return redirect('index')
            else:
                return redirect('index')

        else:
            messages.error(request, "Email or password is incorrect")

    return render(request, 'login.html')


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


def register_teacher(request):
    if request.method == 'POST':
        form = teacher_form(request.POST)
        if form.is_valid():
            user = form.save()
            from onlinestudy.i18n_local import LANGUAGES
            cookie_lang = request.COOKIES.get(settings.SITE_LANG_COOKIE)
            if cookie_lang in LANGUAGES:
                user.language = cookie_lang
                user.save(update_fields=['language'])
            login(request, user)
            return redirect('index')
    else:
        form = teacher_form()

    return render(request, 'teacher_add.html', {'form': form})


# ============================================================
# FORGOT PASSWORD — EMAIL OTP
# ============================================================

SESSION_OTP_EMAIL = 'otp_reset_email'
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
    verified_email = request.session.get(SESSION_OTP_VERIFIED)

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


# ============================================================
# SETTINGS / LANGUAGE
# ============================================================

def setting(request):
    if request.user.is_authenticated:
        return render(request, 'setting.html', {
            'change_password_form': ChangePasswordForm(user=request.user),
        })
    return render(request, 'setting.html')


@login_required
def change_password(request):
    """Settings > Security: change the signed-in user's password.

    Verifies the current password with Django's authenticate-style check,
    validates the new one with the project's AUTH_PASSWORD_VALIDATORS, saves
    it via set_password (proper hashing), and keeps the session: the login
    cycle salts the password hash, so unlike the forgot-password reset this
    does NOT need to re-login.
    """
    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save(update_fields=['password'])
            # Keep the current session valid after the hash change.
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was changed successfully.')
            return redirect('setting')
        messages.error(request, 'Please fix the errors below and try again.')
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, 'setting.html', {
        'change_password_form': form,
        'change_password_open': form.is_bound and (form.errors or None) is not None and not form.is_valid(),
    })


@login_required
@require_POST
def delete_account(request):
    """Settings > Danger zone: permanently delete the signed-in account.

    Requires the account's current password (typed into the styled confirm
    modal) plus CSRF. Related rows cascade (their courses, enrollments,
    comments, AI conversations...); every cascade target references the user
    itself, so nobody else's data is touched. Deleting first then logging out
    is safe: logout only clears the session.
    """
    confirm_password = request.POST.get('confirm_password') or ''
    if not request.user.check_password(confirm_password):
        messages.error(request, 'That password is incorrect. Your account was not deleted.')
        return redirect('setting')

    user = request.user
    user.delete()
    logout(request)
    messages.success(request, 'Your account has been permanently deleted.')
    return redirect('index')


@login_required
@require_POST
def save_language(request):
    """Store the UI language (Settings > Language) on the user, then mirror
    it into LANG_COOKIE so pages that render before login also follow it."""
    from onlinestudy.i18n_local import LANGUAGES

    code = (request.POST.get('language') or '').strip()
    if code not in LANGUAGES:
        return redirect('setting')

    request.user.language = code
    request.user.save(update_fields=['language'])

    response = redirect(request.POST.get('next') or 'setting')
    if response.status_code == 302 and '://' not in response.url:
        response.set_cookie(
            settings.SITE_LANG_COOKIE, code, max_age=365 * 24 * 3600,
            httponly=True, samesite='Lax',
        )
    return response


# ============================================================
# USER PROFILE (works for both students and teachers)
# ============================================================

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
    import urllib.request

    api_messages = [{'role': 'system', 'content': AI_SYSTEM_PROMPT}]
    for m in messages:
        role = 'assistant' if m['role'] == 'assistant' else 'user'
        api_messages.append({'role': role, 'content': m['content']})

    payload = json.dumps({
        'model': settings.DEEPSEEK_MODEL,
        'messages': api_messages,
        'temperature': 0.7,
        'max_tokens': 1024,
        'stream': False,
    }).encode('utf-8')

    request_obj = urllib.request.Request(
        f'{settings.DEEPSEEK_BASE_URL}/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
        },
        method='POST',
    )
    with urllib.request.urlopen(request_obj, timeout=settings.DEEPSEEK_TIMEOUT) as response:
        data = json.loads(response.read().decode('utf-8'))

    try:
        return data['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError('Unexpected DeepSeek API response shape.')


def _get_or_fresh_conversation(request):
    """Resolve which conversation the "AI page" should open.

    ?c=<id> opens that chat (if it belongs to the user); without ?c the
    newest chat opens; ?new=1 opens a blank composer for starting a fresh
    chat (the conversation is only created when the question is actually
    asked). Existing messages with no conversation (pre-feature data or
    direct ORM writes) are shown as one continuing stream when nothing
    is selected.
    """
    if request.GET.get('new') in ('1', 'true'):
        return None, request.user.ai_chat_messages.none()
    conv_id = request.GET.get('c')
    if conv_id is None:
        current = request.user.ai_conversations.first()
    else:
        current = request.user.ai_conversations.filter(id=conv_id).first()
    if current is not None:
        return current, current.messages.all()
    return None, request.user.ai_chat_messages.filter(
        conversation__isnull=True).order_by('created_at')


@login_required
def ai_assistant(request):
    """Chat page with a conversation sidebar (past chats stay listed)."""
    current, history = _get_or_fresh_conversation(request)
    if request.user.role == 'teacher':
        my_courses = Course.objects.filter(student=request.user)
    else:
        my_courses = Course.objects.filter(enrollment__student=request.user)
    return render(request, 'ai_assistant.html', {
        'history': history,
        'current_conversation': current,
        'conversations': (
            request.user.ai_conversations
            .annotate(message_count=Count('messages'))
            .order_by('-updated_at')
        ),
        'ai_enabled': bool(settings.DEEPSEEK_API_KEY),
        'my_courses': my_courses.order_by('title')[:20],
    })


def _user_visible_course(user, course_id):
    """The course with `course_id`, but only if this user is allowed to see it:
    teachers see their own courses (published or draft), students see published
    courses plus what they are enrolled in (same rule as the home page), and
    admins see everything. Returns None otherwise."""
    qs = Course.objects.filter(id=course_id)
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return qs.first()
    if user.role == 'teacher':
        return qs.filter(student=user).first()
    return qs.filter(Q(is_published=True) | Q(student=user) | Q(enrollment__student=user)).first()


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
        course = _user_visible_course(request.user, data.get('course_id'))
    conversation_id = data.get('conversation_id')
    if conversation_id is not None and not str(conversation_id).isdigit():
        conversation_id = None
    conversation = (
        request.user.ai_conversations.filter(id=conversation_id).first()
        if conversation_id else None
    )

    cap = settings.AI_HISTORY_TURNS * 2
    if conversation is not None:
        prior = list(
            conversation.messages.order_by('-created_at')
            .values('role', 'content')[: cap]
        )
    else:
        prior = list(
            request.user.ai_chat_messages
            .filter(conversation__isnull=True)
            .order_by('-created_at').values('role', 'content')[: cap]
        )
    prior.reverse()

    context_text = _ai_course_context(request.user)
    if course is not None:
        context_text += f' The current question is about the course "{course.title}".'
    api_messages = [{'role': 'user', 'content': context_text}]
    api_messages += prior + [{'role': 'user', 'content': question}]

    try:
        reply = _call_deepseek(api_messages)
    except Exception as exc:
        return JsonResponse({
            'success': False,
            'error': 'The AI service is unavailable right now. Please try again shortly.',
            'detail': f'{type(exc).__name__}: {exc}' if settings.DEBUG else '',
        }, status=502)

    if conversation is None:
        title = question if len(question) <= 60 else question[:60] + '…'
        conversation = request.user.ai_conversations.create(title=title)
    reply_payload = {'id': conversation.id, 'title': conversation.title}

    AIChatMessage.objects.bulk_create([
        AIChatMessage(
            user=request.user, conversation=conversation,
            role='user', content=question,
        ),
        AIChatMessage(
            user=request.user, conversation=conversation,
            role='assistant', content=reply,
        ),
    ])
    return JsonResponse({
        'success': True,
        'reply': reply,
        'question': question,
        'conversation': reply_payload,
    })


@login_required
@require_POST
def clear_ai_chat(request):
    """Delete one chat's messages, or (with no conversation_id) everything."""
    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        data = {}

    conversation_id = data.get('conversation_id')
    conversation = (
        request.user.ai_conversations.filter(id=conversation_id).first()
        if conversation_id else None
    )
    if conversation is not None:
        deleted, _ = conversation.messages.all().delete()
    else:
        deleted, _ = request.user.ai_chat_messages.all().delete()
    return JsonResponse({'success': True, 'deleted': deleted})


@login_required
@require_POST
def delete_ai_conversation(request):
    """Remove one sidebar chat entirely (its messages go with it)."""
    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        data = {}

    conversation = request.user.ai_conversations.filter(
        id=data.get('conversation_id')).first()
    if conversation is None:
        return JsonResponse(
            {'success': False, 'error': 'Chat not found.'}, status=404)
    deleted = conversation.messages.count()  # owner-scoped count
    conversation.delete()
    return JsonResponse({'success': True, 'deleted': deleted})
