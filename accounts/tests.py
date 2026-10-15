import json
import shutil
import tempfile

from unittest import mock
from urllib.error import HTTPError

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, PasswordResetOTP, AIChatMessage
from teacher.models import Course, Quiz, Playlist, Question
from student.models import Enrollment, CourseOrder, Comment, Like, QuizAttempt
from adminpanel.views import _build_analytics
from teacher.views import _build_teacher_analytics
from onlinestudy.i18n_local import t as translate, LANGUAGES


def make_user(email, password='Passw0rd!123', **extra):
    return User.objects.create_user(email=email, password=password, **extra)


class AuthedTestCase(TestCase):
    """Helpers shared by the tests below."""

    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_user(
            'teacher@example.com', role='teacher', first_name='T', last_name='Eacher',
        )
        cls.student = make_user(
            'student@example.com', role='student', first_name='S', last_name='Tudent',
        )
        cls.superuser = make_user(
            'admin@example.com', role='student', is_superuser=True, is_staff=True,
        )

    def login(self, user):
        self.client.force_login(user)


class TempMediaMixin:
    """For classes decorated with @override_settings(MEDIA_ROOT=...):
    removes the throwaway media dir after the class has run."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        media = (getattr(cls, '_overridden_settings', {}) or {}).get('MEDIA_ROOT')
        if media:
            shutil.rmtree(media, ignore_errors=True)


class AdminDashboardAccessTest(AuthedTestCase):
    """The admin dashboard must only be visible to superusers."""

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_regular_student_is_blocked(self):
        self.login(self.student)
        response = self.client.get(reverse('admin_dashboard'))
        # Not a 200 page leak: the student is bounced to the index.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))
        self.assertFalse(response.wsgi_request.user.is_superuser)

    def test_teacher_is_blocked(self):
        self.login(self.teacher)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_superuser_can_access(self):
        self.login(self.superuser)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_stays_open_for_superuser_with_admin_button(self):
        """Back-to-Home must reach the index for admins too (no redirect loop),
        and the header admin-dashboard button must render for superusers only."""
        self.login(self.superuser)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin_dashboard'))

        # The button must not leak to students, teachers or anonymous visitors.
        self.login(self.student)
        self.assertNotContains(
            self.client.get(reverse('index')), reverse('admin_dashboard'))
        self.login(self.teacher)
        self.assertNotContains(
            self.client.get(reverse('index')), reverse('admin_dashboard'))
        self.client.logout()
        self.assertNotContains(
            self.client.get(reverse('index')), reverse('admin_dashboard'))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PriviewAccessTest(TempMediaMixin, AuthedTestCase):
    """Draft courses must not be visible to people who do not own them."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.draft = Course.objects.create(
            student=cls.teacher, title='Draft Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=False,
        )
        cls.published = Course.objects.create(
            student=cls.teacher, title='Published Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )

    def test_anonymous_cannot_see_draft(self):
        response = self.client.get(reverse('priview', args=[self.draft.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_student_cannot_see_draft(self):
        self.login(self.student)
        response = self.client.get(reverse('priview', args=[self.draft.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_owner_can_see_own_draft(self):
        self.login(self.teacher)
        response = self.client.get(reverse('priview', args=[self.draft.id]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_see_draft(self):
        self.login(self.superuser)
        response = self.client.get(reverse('priview', args=[self.draft.id]))
        self.assertEqual(response.status_code, 200)

    def test_anyone_can_see_published(self):
        response = self.client.get(reverse('priview', args=[self.published.id]))
        self.assertEqual(response.status_code, 200)

    def test_page_renders_without_video_file(self):
        # Regression: {{ course.vedio.url }} crashed for courses with no video.
        response = self.client.get(reverse('priview', args=[self.published.id]))
        self.assertEqual(response.status_code, 200)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class EnrollDraftCourseTest(TempMediaMixin, AuthedTestCase):
    """Students must not be able to enroll into unpublished draft courses."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.draft = Course.objects.create(
            student=cls.teacher, title='Draft', category='python',
            level='beginner', Course_price=0, description='x', is_published=False,
        )
        cls.published = Course.objects.create(
            student=cls.teacher, title='Published', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )

    def test_cannot_enroll_in_draft(self):
        self.login(self.student)
        response = self.client.post(reverse('enroll_course', args=[self.draft.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Enrollment.objects.filter(student=self.student, course=self.draft).exists()
        )

    def test_cannot_enroll_in_draft_via_ajax(self):
        self.login(self.student)
        response = self.client.post(
            reverse('enroll_course', args=[self.draft.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Enrollment.objects.filter(student=self.student, course=self.draft).exists()
        )

    def test_can_enroll_in_published(self):
        from unittest import mock

        self.login(self.student)
        # Simulate the full HesabPay checkout + webhook success flow.
        with mock.patch('hesabpay.services.checkout.HesabPayClient') as mock_client_cls:
            mock_client_cls.return_value.create_session.return_value = {
                'url': 'https://test.hesabpay.com/checkout/fake'
            }
            response = self.client.post(
                reverse('enroll_course', args=[self.published.id]),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'checkout')
        order = CourseOrder.objects.get(student=self.student, course=self.published)
        from student.payments import simulate_hesabpay_success
        with self.captureOnCommitCallbacks(execute=True):
            simulate_hesabpay_success(order)
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, course=self.published).exists()
        )


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class QuizAttemptLimitTest(TempMediaMixin, AuthedTestCase):
    """Quiz.attempts_allowed must actually limit how often a student submits."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.course = Course.objects.create(
            student=cls.teacher, title='Quiz Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        cls.quiz = Quiz.objects.create(
            course=cls.course, teacher=cls.teacher,
            title='Limited Quiz', is_published=True, attempts_allowed='1',
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)

    def submit(self):
        return self.client.post(
            reverse('submit_quiz'),
            data=json.dumps({'quiz_id': self.quiz.id, 'answers': []}),
            content_type='application/json',
        )

    def test_first_attempt_succeeds(self):
        self.login(self.student)
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    def test_second_attempt_is_blocked(self):
        self.login(self.student)
        first = self.submit()
        self.assertEqual(first.status_code, 200)
        second = self.submit()
        self.assertEqual(second.status_code, 403)
        self.assertIn('attempt', second.json()['message'])

    def test_unlimited_attempts_never_block(self):
        self.quiz.attempts_allowed = 'Unlimited'
        self.quiz.save()
        self.login(self.student)
        for _ in range(3):
            self.assertEqual(self.submit().status_code, 200)

    def test_non_enrolled_student_cannot_submit(self):
        outsider = make_user('outsider@example.com')
        self.login(outsider)
        response = self.submit()
        self.assertEqual(response.status_code, 403)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DeleteCourseTest(TempMediaMixin, AuthedTestCase):
    """Course deletion needs login, POST, and ownership."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.course = Course.objects.create(
            student=cls.teacher, title='Doomed', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )

    def test_anonymous_cannot_delete(self):
        response = self.client.post(reverse('delet_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_get_request_is_rejected(self):
        self.login(self.teacher)
        response = self.client.get(reverse('delet_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_non_owner_cannot_delete(self):
        self.login(self.student)
        response = self.client.post(reverse('delet_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_owner_can_delete(self):
        self.login(self.teacher)
        response = self.client.post(reverse('delet_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class IndexPageTest(TempMediaMixin, AuthedTestCase):
    """The homepage must render courses without videos and stay fast."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Course.objects.create(
            student=cls.teacher, title='No Video', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )

    def test_index_renders_videoless_course(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Video')

    def test_draft_courses_hidden_from_anonymous(self):
        self.login(self.teacher)  # owns no published course here; create draft
        Course.objects.create(
            student=self.teacher, title='Hidden Draft', category='python',
            level='beginner', Course_price=0, description='x', is_published=False,
        )
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Hidden Draft')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AddPlaylistApiTest(TempMediaMixin, AuthedTestCase):
    """Server side of the Add Video button."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.course = Course.objects.create(
            student=cls.teacher, title='API Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        cls.other_course = Course.objects.create(
            student=cls.student, title='Other Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )

    def video_file(self):
        # A tiny but structurally valid-enough mp4 header; the view only checks
        # extension/MIME, so the bytes just need to exist.
        return SimpleUploadedFile(
            'lesson.mp4', b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4',
        )

    def test_owner_can_upload(self):
        self.login(self.teacher)
        response = self.client.post(
            reverse('add_playlist', args=[self.course.id]),
            {'video': self.video_file()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(Playlist.objects.filter(course=self.course).count(), 1)

    def test_non_owner_cannot_upload(self):
        self.login(self.student)
        response = self.client.post(
            reverse('add_playlist', args=[self.course.id]),
            {'video': self.video_file()},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Playlist.objects.count(), 0)

    def test_no_file_returns_400(self):
        self.login(self.teacher)
        response = self.client.post(reverse('add_playlist', args=[self.course.id]), {})
        self.assertEqual(response.status_code, 400)


class ExplodingEmailBackend:
    """An SMTP-shaped backend that always fails, for the honest-error-path test."""

    def __init__(self, *args, **kwargs):
        pass

    def open(self):
        return False

    def close(self):
        pass

    def send_messages(self, messages):
        raise RuntimeError('SMTP unreachable (test backend)')


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_CONSOLE_MODE=False,
)
class ForgotPasswordOTPFlowTest(AuthedTestCase):
    """End-to-end coverage of the email-OTP password reset."""

    def request_code(self, email):
        return self.client.post(reverse('forgot_password'), {
            'step': 'request', 'email': email,
        })

    def code_from_outbox(self):
        # Subject looks like 'Your password reset code: 123456'.
        return mail.outbox[-1].subject.rsplit(' ', 1)[-1]

    def test_request_sends_real_email(self):
        response = self.request_code(self.student.email)
        self.assertContains(response, 'Enter it below')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.student.email])
        self.assertRegex(self.code_from_outbox(), r'\d{6}')

    def test_unknown_email_is_not_revealed(self):
        response = self.request_code('nobody@example.com')
        self.assertContains(response, 'Enter it below')
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(PasswordResetOTP.objects.exists())

    def test_wrong_code_is_rejected(self):
        self.request_code(self.student.email)
        code = self.code_from_outbox()
        wrong = '000000' if code != '000000' else '111111'
        response = self.client.post(reverse('forgot_password'), {
            'step': 'verify', 'code': wrong,
        })
        self.assertContains(response, 'not correct')
        self.assertEqual(PasswordResetOTP.objects.latest('created_at').attempts, 1)

    def test_full_flow_resets_password_and_logs_in(self):
        self.request_code(self.student.email)
        self.client.post(reverse('forgot_password'), {
            'step': 'verify', 'code': self.code_from_outbox(),
        })
        response = self.client.post(reverse('forgot_password'), {
            'step': 'password',
            'new_password1': 'BrandNew!Pass9',
            'new_password2': 'BrandNew!Pass9',
        })
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(PasswordResetOTP.objects.latest('created_at').is_used)
        self.client.logout()
        self.assertTrue(
            self.client.login(email=self.student.email, password='BrandNew!Pass9')
        )

    def test_send_failure_is_reported_and_nothing_is_stored(self):
        with override_settings(EMAIL_BACKEND='accounts.tests.ExplodingEmailBackend'):
            response = self.request_code(self.student.email)
        self.assertContains(response, 'could not send the email')
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(PasswordResetOTP.objects.exists())
        self.assertIsNone(self.client.session.get('otp_reset_email'))

    def test_console_mode_notice_mentions_terminal_only(self):
        with override_settings(EMAIL_CONSOLE_MODE=True):
            response = self.request_code(self.student.email)
        self.assertContains(response, 'Development mode')

    def test_code_is_never_rendered_in_html(self):
        """The OTP must live only in the email (or the server terminal in
        console mode) - never in any HTML the browser receives."""
        self.request_code(self.student.email)
        code = self.code_from_outbox()
        for step_payload in (
            {'step': 'request', 'email': self.student.email},
            {'step': 'verify', 'code': '000000'},
        ):
            response = self.client.post(reverse('forgot_password'), step_payload)
            self.assertNotContains(response, code, status_code=200)
            self.assertNotContains(response, 'otp_dev_code')
            self.assertIsNone(self.client.session.get('otp_dev_code'))

    def test_check_email_command_issues_otp(self):
        # check_email <email> --otp sends the OTP email, then its own test mail.
        call_command('check_email', self.student.email, '--otp', verbosity=0)
        self.assertEqual(len(mail.outbox), 2)


@override_settings(
    DEEPSEEK_API_KEY='test-key',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_CONSOLE_MODE=False,
)
class AIAssistantTest(AuthedTestCase):
    """The AI study assistant page and the ask/clear endpoints."""

    def ask(self, question='What is a loop?', course_id=None, conversation_id=None):
        return self.client.post(
            reverse('ask_ai'),
            data=json.dumps({
                'question': question,
                'course_id': course_id,
                'conversation_id': conversation_id,
            }),
            content_type='application/json',
        )

    def patched_deepseek(self, reply='A loop repeats instructions.'):
        return mock.patch(
            'accounts.views._call_deepseek', return_value=reply,
        )

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('ai_assistant'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_page_shows_history_and_courses(self):
        AIChatMessage.objects.create(
            user=self.student, role='user', content='What is recursion?')
        AIChatMessage.objects.create(
            user=self.student, role='assistant', content='It calls itself.')
        course = Course.objects.create(
            student=self.teacher, title='Python 101', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        Enrollment.objects.create(student=self.student, course=course)

        self.login(self.student)
        response = self.client.get(reverse('ai_assistant'))
        self.assertContains(response, 'What is recursion?')
        self.assertContains(response, 'Python 101')

    def test_ask_persists_question_and_reply(self):
        self.login(self.student)
        with self.patched_deepseek():
            response = self.ask()
        self.assertTrue(response.json()['success'])
        self.assertEqual(
            [m.role for m in AIChatMessage.objects.filter(user=self.student)],
            ['user', 'assistant'],
        )
        self.assertEqual(response.json()['reply'], 'A loop repeats instructions.')

    def test_empty_question_is_rejected(self):
        self.login(self.student)
        response = self.ask('   ')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AIChatMessage.objects.exists())

    def test_too_long_question_is_rejected(self):
        self.login(self.student)
        response = self.ask('x' * 2001)
        self.assertEqual(response.status_code, 400)

    def test_course_is_scoped_to_enrollments(self):
        self.login(self.student)
        with self.patched_deepseek() as deepseek:
            self.ask(course_id=999)
        # A non-existent id must not inject anything into the conversation.
        sent = deepseek.call_args[0][0]
        self.assertEqual(len(sent), 2)  # context + question only

    def test_visible_course_is_mentioned_in_context(self):
        """A course the user may see is passed to the AI via the context line,
        with no fake assistant turn breaking the conversation alternation."""
        course = Course.objects.create(
            student=self.teacher, title='Visible 101', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        self.login(self.student)
        with self.patched_deepseek() as deepseek:
            self.ask(course_id=course.id)
        sent = deepseek.call_args[0][0]
        self.assertEqual(len(sent), 2)  # context + question
        self.assertIn('Visible 101', sent[0]['content'])
        self.assertEqual([m['role'] for m in sent], ['user', 'user'])

    def test_other_users_draft_course_is_not_leaked(self):
        """Passing someone else's unpublished course id must not reveal it.
        Regression guard: course ids used to be accepted without any scoping."""
        hidden = Course.objects.create(
            student=self.teacher, title='Secret Draft', category='python',
            level='beginner', Course_price=0, description='x', is_published=False,
        )
        self.login(self.student)
        with self.patched_deepseek() as deepseek:
            self.ask(course_id=hidden.id)
        sent = deepseek.call_args[0][0]
        self.assertEqual(len(sent), 2)
        self.assertNotIn('Secret Draft', ' '.join(m['content'] for m in sent))

    def test_teacher_picks_their_own_draft_course(self):
        draft = Course.objects.create(
            student=self.teacher, title='My Draft Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=False,
        )
        self.login(self.teacher)
        with self.patched_deepseek() as deepseek:
            self.ask(course_id=draft.id)
        sent = deepseek.call_args[0][0]
        self.assertEqual(len(sent), 2)
        self.assertIn('My Draft Course', sent[0]['content'])

    def test_history_is_replayed_with_a_cap(self):
        for i in range(15):
            AIChatMessage.objects.create(
                user=self.student, role='user', content=f'q{i}')
            AIChatMessage.objects.create(
                user=self.student, role='assistant', content=f'a{i}')
        self.login(self.student)
        with self.patched_deepseek() as deepseek:
            self.ask('and now?')
        sent = deepseek.call_args[0][0]
        # context + 10 turns*2 + new question
        self.assertEqual(len(sent), 1 + 20 + 1)
        self.assertEqual(sent[-1]['content'], 'and now?')

    def test_deepseek_failure_returns_502_and_stores_nothing(self):
        self.login(self.student)
        with mock.patch(
            'accounts.views._call_deepseek',
            side_effect=RuntimeError('boom'),
        ):
            response = self.ask()
        self.assertEqual(response.status_code, 502)
        self.assertFalse(AIChatMessage.objects.exists())

    def test_clear_deletes_only_own_history(self):
        AIChatMessage.objects.create(
            user=self.teacher, role='user', content='teacher q')
        AIChatMessage.objects.create(
            user=self.student, role='user', content='student q')
        self.login(self.student)
        response = self.client.post(reverse('clear_ai_chat'))
        self.assertTrue(response.json()['success'])
        self.assertFalse(
            AIChatMessage.objects.filter(user=self.student).exists())
        self.assertTrue(
            AIChatMessage.objects.filter(user=self.teacher).exists())

    def test_deepseek_http_404_maps_to_friendly_502(self):
        self.login(self.student)
        with mock.patch(
            'accounts.views._call_deepseek',
            side_effect=HTTPError('url', 404, 'Not Found', hdrs=None, fp=None),
        ):
            response = self.ask()
        self.assertEqual(response.status_code, 502)
        self.assertIn('unavailable', response.json()['error'])

    def ask_conversation(self, conversation_id=None):
        with self.patched_deepseek():
            response = self.ask(conversation_id=conversation_id)
        self.assertEqual(response.status_code, 200)
        return response

    def test_first_ask_creates_titled_conversation(self):
        self.login(self.student)
        response = self.ask_conversation()
        payload = response.json()
        conv = self.student.ai_conversations.get()
        self.assertEqual(payload['conversation']['id'], conv.id)
        self.assertEqual(payload['conversation']['title'], conv.title)
        self.assertEqual(conv.messages.count(), 2)  # user turn + reply
        self.assertEqual(AIChatMessage.objects.count(), 2)

    def test_asking_again_appends_to_same_conversation(self):
        """With conversation_id in the payload, the chat continues in place."""
        self.login(self.student)
        first = self.ask_conversation()
        conv_id = first.json()['conversation']['id']
        with self.patched_deepseek(reply='second reply'):
            response = self.ask(conversation_id=conv_id)
        self.assertEqual(response.json()['conversation']['id'], conv_id)
        conv = self.student.ai_conversations.get(pk=conv_id)
        self.assertEqual(conv.messages.count(), 4)
        self.assertEqual(self.student.ai_conversations.count(), 1)

    def test_sidebar_lists_and_opens_conversations(self):
        conv = self.student.ai_conversations.create(title='Quadratic help')
        other = self.teacher.ai_conversations.create(title='Teacher private')
        self.login(self.student)
        response = self.client.get(reverse('ai_assistant'))
        self.assertContains(response, 'Quadratic help')
        self.assertNotContains(response, 'Teacher private')

        # Opening someone else's chat id must not leak their messages.
        winding = self.client.get(reverse('ai_assistant'), {'c': other.id})
        self.assertNotContains(winding, 'Teacher private')

    def test_new_chat_opens_blank_composer(self):
        conv = self.student.ai_conversations.create(title='Quadratic help')
        AIChatMessage.objects.create(
            user=self.student, conversation=conv, role='user', content='x')
        self.login(self.student)
        response = self.client.get(reverse('ai_assistant'), {'new': '1'})
        self.assertContains(response, 'ai-empty')
        # And the newest chat still shows by default without ?new=1
        default = self.client.get(reverse('ai_assistant'))
        self.assertContains(default, 'Quadratic help')

    def test_clear_single_conversation_only(self):
        c1 = self.student.ai_conversations.create(title='one')
        c2 = self.student.ai_conversations.create(title='two')
        AIChatMessage.objects.create(
            user=self.student, conversation=c1, role='user', content='a')
        AIChatMessage.objects.create(
            user=self.student, conversation=c2, role='user', content='b')
        self.login(self.student)
        response = self.client.post(
            reverse('clear_ai_chat'),
            data=json.dumps({'conversation_id': c1.id}),
            content_type='application/json',
        )
        self.assertTrue(response.json()['success'])
        self.assertFalse(c1.messages.exists())
        self.assertTrue(c2.messages.exists())

    def test_delete_conversation_is_owner_scoped(self):
        own = self.student.ai_conversations.create(title='mine')
        foreign = self.teacher.ai_conversations.create(title='theirs')
        foreign_msg = AIChatMessage.objects.create(
            user=self.teacher, conversation=foreign, role='user', content='q')
        self.login(self.student)

        response = self.client.post(
            reverse('delete_ai_conversation'),
            data=json.dumps({'conversation_id': foreign.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            AIChatMessage.objects.filter(pk=foreign_msg.pk).exists())

        response = self.client.post(
            reverse('delete_ai_conversation'),
            data=json.dumps({'conversation_id': own.id}),
            content_type='application/json',
        )
        self.assertTrue(response.json()['success'])
        self.assertFalse(
            self.student.ai_conversations.filter(pk=own.id).exists())


@override_settings(
    DEEPSEEK_API_KEY='test-key',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_CONSOLE_MODE=False,
)
class AdminAnalyticsTest(AuthedTestCase):
    """Superuser-only platform data analysis report + CSV export."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.course = Course.objects.create(
            student=cls.teacher, title='Analytics Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)
        Like.objects.create(user=cls.student, course=cls.course)
        Comment.objects.create(user=cls.student, course=cls.course, text='nice')

    def test_anonymous_is_redirected(self):
        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_student_and_teacher_are_blocked(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse('admin_analytics')).status_code, 302)
        self.assertEqual(
            self.client.get(reverse('admin_analytics_csv')).status_code, 403)
        self.login(self.teacher)
        self.assertEqual(self.client.get(reverse('admin_analytics')).status_code, 302)
        self.assertEqual(
            self.client.get(reverse('admin_analytics_csv')).status_code, 403)

    def test_superuser_sees_report_with_real_numbers(self):
        self.login(self.superuser)
        response = self.client.get(reverse('admin_analytics'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Platform Analytics', content)
        self.assertIn('Analytics Course', content)
        self.assertIn('teacher@example.com', content)   # top teachers table
        self.assertIn('student@example.com', content)   # active students table

    def test_overview_counts_are_correct(self):
        report = _build_analytics()
        self.assertGreaterEqual(report['overview']['courses'], 1)
        self.assertGreaterEqual(report['overview']['enrollments'], 1)
        self.assertGreaterEqual(report['overview']['likes'], 1)
        self.assertGreaterEqual(report['overview']['comments'], 1)
        self.assertEqual(len(report['daily']), 14)
        self.assertGreaterEqual(report['courses_max'], 1)

    def test_csv_export_contains_sections(self):
        self.login(self.superuser)
        response = self.client.get(reverse('admin_analytics_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        text = response.content.decode()
        self.assertIn('OVERVIEW', text)
        self.assertIn('DAILY ACTIVITY', text)
        self.assertIn('TOP COURSES BY ENGAGEMENT', text)
        self.assertIn('QUIZ PERFORMANCE', text)
        self.assertIn('RECENT ENROLLMENTS', text)
        self.assertIn('Analytics Course', text)


@override_settings(
    DEEPSEEK_API_KEY='test-key',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_CONSOLE_MODE=False,
)
class TeacherAnalyticsTest(AuthedTestCase):
    """Teacher's own data analysis report: strictly scoped + CSV export."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.teacher2 = make_user('teacher2@example.com', role='teacher')
        cls.student2 = make_user('student2@example.com', role='student')

        # This teacher's course, with one enrolled student, engagement,
        # a quiz and one submitted (perfect) attempt.
        cls.course = Course.objects.create(
            student=cls.teacher, title='Teacher Analytics Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        cls.other_course = Course.objects.create(
            student=cls.teacher2, title='Other Teachers Course', category='python',
            level='beginner', Course_price=0, description='x', is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)
        Enrollment.objects.create(student=cls.student2, course=cls.other_course)
        Like.objects.create(user=cls.student, course=cls.course)
        Comment.objects.create(user=cls.student, course=cls.course, text='nice')

        cls.quiz = Quiz.objects.create(
            course=cls.course, teacher=cls.teacher, title='Teacher Quiz',
            is_published=True,
        )
        Question.objects.create(quiz=cls.quiz, question_type='mc', text='2+2?', points=2)
        cls.quiz2 = Quiz.objects.create(
            course=cls.other_course, teacher=cls.teacher2, title='Other Quiz',
            is_published=True,
        )
        cls.attempt = QuizAttempt.objects.create(
            quiz=cls.quiz, student=cls.student, score=2, status='submitted',
            submitted_at=timezone.now(),
        )

    def test_anonymous_is_redirected(self):
        response = self.client.get(reverse('teacher_analytics'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_student_is_blocked(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse('teacher_analytics')).status_code, 302)
        self.assertEqual(
            self.client.get(reverse('teacher_analytics_csv')).status_code, 403)

    def test_teacher_sees_own_report(self):
        self.login(self.teacher)
        response = self.client.get(reverse('teacher_analytics'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('My Data Analysis', content)
        self.assertIn('Teacher Analytics Course', content)
        self.assertIn('Teacher Quiz', content)
        # Other people's data must not leak in.
        self.assertNotIn('Other Teachers Course', content)
        self.assertNotIn('Other Quiz', content)
        self.assertNotIn('teacher2@example.com', content)

    def test_superuser_may_preview(self):
        self.login(self.superuser)
        self.assertEqual(self.client.get(reverse('teacher_analytics')).status_code, 200)

    def test_report_is_scoped_to_own_data(self):
        report = _build_teacher_analytics(self.teacher)
        self.assertEqual(
            [c.title for c in report['course_rows']], ['Teacher Analytics Course'])
        self.assertEqual(report['overview']['courses'], 1)
        self.assertEqual(report['overview']['enrollments'], 1)
        self.assertEqual(report['overview']['likes'], 1)
        self.assertEqual(report['overview']['comments'], 1)
        self.assertEqual(report['overview']['quizzes'], 1)
        self.assertEqual(
            [row['quiz'].title for row in report['quiz_rows']], ['Teacher Quiz'])
        # The student active in the OTHER teacher's course must not appear.
        self.assertEqual(
            [s.email for s in report['top_students']], ['student@example.com'])

    def test_quiz_metrics_are_computed(self):
        report = _build_teacher_analytics(self.teacher)
        self.assertEqual(report['overview']['submitted_attempts'], 1)
        self.assertEqual(report['overview']['pass_rate'], 100.0)
        self.assertEqual(report['overview']['avg_score'], 100.0)
        row = report['quiz_rows'][0]
        self.assertEqual(row['finished'], 1)
        self.assertEqual(row['passed'], 1)
        self.assertEqual(row['avg_pct'], 100.0)

    def test_second_teacher_gets_their_own_scope(self):
        report = _build_teacher_analytics(self.teacher2)
        self.assertEqual(
            [c.title for c in report['course_rows']], ['Other Teachers Course'])
        self.assertEqual(report['overview']['enrollments'], 1)
        self.assertEqual(report['overview']['quiz_attempts'], 0)
        self.assertEqual(report['quiz_summary']['submitted'], 0)
        self.assertEqual(report['quiz_summary']['pass_rate'], 0)

    def test_csv_export_contains_sections(self):
        self.login(self.teacher)
        response = self.client.get(reverse('teacher_analytics_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        text = response.content.decode()
        self.assertIn('Teacher Data Analysis Report', text)
        self.assertIn('teacher@example.com', text)
        self.assertIn('OVERVIEW', text)
        self.assertIn('MY COURSES', text)
        self.assertIn('QUIZ PERFORMANCE', text)
        self.assertIn('MOST ACTIVE STUDENTS', text)
        self.assertIn('RECENT ENROLLMENTS', text)
        self.assertIn('Teacher Analytics Course', text)
        self.assertNotIn('Other Teachers Course', text)

    def test_csv_blocked_for_students(self):
        self.login(self.student)
        self.assertEqual(
            self.client.get(reverse('teacher_analytics_csv')).status_code, 403)


class LanguageSwitchTest(AuthedTestCase):
    """English / Persian (Dari) / Pashto switcher on the Settings page."""

    def reset_language(self, user, code='en'):
        User.objects.filter(pk=user.pk).update(language=code)
        user.refresh_from_db()

    def test_language_defaults_to_english(self):
        self.assertEqual(self.student.language, 'en')

    def test_setting_page_shows_all_three_languages(self):
        self.login(self.student)
        response = self.client.get(reverse('setting'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="langSelect"', html)
        self.assertIn('English', html)
        self.assertIn('\u0641\u0627\u0631\u0633\u06cc', html)   # فارسی
        self.assertIn('\u067e\u069a\u062a\u0648', html)       # پښتو

    def test_choosing_persian_saves_user_and_renders_rtl(self):
        self.reset_language(self.student)
        self.login(self.student)
        response = self.client.post(reverse('save_language'), {'language': 'fa'})
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.language, 'fa')

        page = self.client.get(reverse('setting'))
        html = page.content.decode()
        self.assertEqual(page.context['lang'], 'fa')
        self.assertEqual(page.context['lang_dir'], 'rtl')
        self.assertIn('dir="rtl"', html)
        self.assertNotIn('dir="ltr"', html)
        self.assertIn('\u062a\u0646\u0638\u06cc\u0645\u0627\u062a', html)  # تنظیمات

    def test_cookie_seeds_login_page_and_new_login(self):
        self.reset_language(self.student)
        # Anonymous visitor with the language cookie (picked before login).
        self.client.cookies['site_lang'] = 'ps'
        page = self.client.get(reverse('user_login'))
        self.assertEqual(page.context['lang'], 'ps')
        html = page.content.decode()
        self.assertIn('dir="rtl"', html)
        self.assertIn('\u0646\u0646\u0648\u062a\u0644', html)  # ننوتل (Sign In)

        # Logging in adopts that choice into the user profile.
        self.client.post(
            reverse('user_login'),
            {'email': 'student@example.com', 'password': 'Passw0rd!123'},
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.language, 'ps')

    def test_invalid_language_is_rejected(self):
        self.reset_language(self.student)
        self.login(self.student)
        response = self.client.post(reverse('save_language'), {'language': 'xx'})
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.language, 'en')

    def test_pashto_strings_work_and_fallback_to_english(self):
        self.assertEqual(translate('fa', 'logout'), '\u062e\u0631\u0648\u062c')
        self.assertEqual(translate('ps', 'login'), '\u0646\u0646\u0648\u062a\u0644')
        self.assertEqual(translate('en', 'logout'), 'Logout')
        # Unknown keys degrade to empty string instead of crashing a page.
        self.assertEqual(translate('fa', 'made_up_key'), '')
        self.assertEqual(set(LANGUAGES), {'en', 'fa', 'ps'})


# ============================================================
# SETTINGS / PROFILE / NOTIFICATIONS / PLAYLIST MANAGEMENT
# ============================================================

import io
import os

from django.test import Client
from PIL import Image

from accounts.models import Notification, ProfileImg
from accounts.notifications import notify


NEW_PASSWORD = 'Gr33n-Meadow-Lantern!'


class ChangePasswordTest(AuthedTestCase):
    url = reverse('change_password')

    def post(self, old='Passw0rd!123', new1=NEW_PASSWORD, new2=NEW_PASSWORD):
        return self.client.post(self.url, {
            'old_password': old, 'new_password1': new1, 'new_password2': new2,
        })

    def test_success_changes_password_and_keeps_session(self):
        self.login(self.student)
        response = self.post()
        self.assertRedirects(response, reverse('setting'))
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password(NEW_PASSWORD))
        # Session survives the hash change.
        page = self.client.get(reverse('user_profile'))
        self.assertEqual(page.status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.student, kind='security').exists())

    def test_wrong_current_password(self):
        self.login(self.student)
        response = self.post(old='not-my-password')
        self.assertEqual(response.status_code, 400)
        self.assertIn('old_password', response.context['change_password_form'].errors)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('Passw0rd!123'))

    def test_mismatched_new_passwords(self):
        self.login(self.student)
        response = self.post(new2=NEW_PASSWORD + 'x')
        self.assertEqual(response.status_code, 400)
        self.assertIn('new_password2', response.context['change_password_form'].errors)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('Passw0rd!123'))

    def test_password_validators_apply(self):
        self.login(self.student)
        for weak in ('12345678', 'password', 'short'):
            response = self.post(new1=weak, new2=weak)
            self.assertEqual(response.status_code, 400, weak)
            self.assertTrue(response.context['change_password_form'].errors, weak)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('Passw0rd!123'))

    def test_settings_page_renders_form_errors(self):
        self.login(self.student)
        response = self.post(old='nope')
        self.assertContains(response, 'field-error', status_code=400)

    def test_anonymous_redirected_to_login(self):
        response = self.post()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        response = client.post(self.url, {
            'old_password': 'Passw0rd!123', 'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD,
        })
        self.assertEqual(response.status_code, 403)

    def test_anonymous_settings_page_hides_security_forms(self):
        response = self.client.get(reverse('setting'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="old_password"')
        self.assertNotContains(response, 'id="deleteAccountModal"')


class DeleteAccountTest(AuthedTestCase):
    url = reverse('delete_account')

    def make_course(self, owner, **extra):
        return Course.objects.create(
            student=owner, title='C', category='python', level='beginner',
            Course_price=0, description='x', is_published=True, **extra,
        )

    def test_correct_password_deletes_and_logs_out(self):
        user = make_user('leaver@example.com')
        course = self.make_course(self.teacher)
        Enrollment.objects.create(student=user, course=course)
        Enrollment.objects.create(student=self.student, course=course)
        self.login(user)
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(email='leaver@example.com').exists())
        # Shared course and other students' records are untouched.
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=course).exists())
        # Session invalidated.
        self.assertEqual(self.client.get(reverse('user_profile')).status_code, 302)

    def test_wrong_password_keeps_account(self):
        self.login(self.student)
        response = self.client.post(self.url, {'confirm_password': 'wrong'})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.context['delete_account_open'])
        self.assertContains(response, 'That password is incorrect', status_code=400)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())

    def test_empty_password_keeps_account(self):
        self.login(self.student)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())

    def test_get_not_allowed(self):
        self.login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())

    def test_anonymous_redirected(self):
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('user_login'), response.url)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        response = client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())

    def test_superuser_is_protected(self):
        self.login(self.superuser)
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.superuser.pk).exists())

    def test_teacher_with_enrolled_students_is_blocked(self):
        course = self.make_course(self.teacher)
        Enrollment.objects.create(student=self.student, course=course)
        self.login(self.teacher)
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.teacher.pk).exists())
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=course).exists())

    def test_teacher_with_others_comments_is_blocked(self):
        course = self.make_course(self.teacher)
        Comment.objects.create(course=course, user=self.student, text='hi')
        self.login(self.teacher)
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(user=self.student).exists())

    def test_settings_page_lists_blockers_and_disables_button(self):
        course = self.make_course(self.teacher)
        Enrollment.objects.create(student=self.student, course=course)
        self.login(self.teacher)
        response = self.client.get(reverse('setting'))
        self.assertTrue(response.context['delete_account_blockers'])
        self.assertContains(response, 'danger-blockers')

    def test_teacher_without_learners_can_delete_own_courses_only(self):
        teacher = make_user('solo@example.com', role='teacher')
        own = self.make_course(teacher)
        other = self.make_course(self.teacher)
        self.login(teacher)
        response = self.client.post(self.url, {'confirm_password': 'Passw0rd!123'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(pk=own.pk).exists())
        self.assertTrue(Course.objects.filter(pk=other.pk).exists())


def png_upload(name='avatar.png', size=(10, 10)):
    buf = io.BytesIO()
    Image.new('RGB', size, (93, 156, 89)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class EditProfileTest(TempMediaMixin, AuthedTestCase):
    url = reverse('edit_profile')

    def test_update_name_and_email(self):
        self.login(self.student)
        response = self.client.post(self.url, {
            'first_name': '  Sara ', 'last_name': 'Green', 'email': 'sara@example.com',
        })
        self.assertRedirects(response, reverse('user_profile'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Sara')
        self.assertEqual(self.student.last_name, 'Green')
        self.assertEqual(self.student.email, 'sara@example.com')
        # Still signed in after changing the login email.
        self.assertEqual(self.client.get(reverse('user_profile')).status_code, 200)

    def test_profile_page_has_edit_form(self):
        self.login(self.student)
        response = self.client.get(reverse('user_profile'))
        self.assertContains(response, 'id="profileModal"')
        self.assertContains(response, 'value="student@example.com"')

    def test_duplicate_email_rejected_case_insensitive(self):
        self.login(self.student)
        response = self.client.post(self.url, {
            'first_name': 'S', 'last_name': 'T', 'email': 'TEACHER@example.com',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.context['edit_profile_form'].errors)
        self.assertTrue(response.context['edit_profile_open'])
        self.student.refresh_from_db()
        self.assertEqual(self.student.email, 'student@example.com')

    def test_invalid_email_and_long_name_rejected(self):
        self.login(self.student)
        response = self.client.post(self.url, {
            'first_name': 'x' * 31, 'last_name': 'T', 'email': 'not-an-email',
        })
        self.assertEqual(response.status_code, 400)
        errors = response.context['edit_profile_form'].errors
        self.assertIn('email', errors)
        self.assertIn('first_name', errors)
        # Rejected values never leak into the rendered personal info.
        self.assertEqual(response.context['info'].email, 'student@example.com')

    def test_picture_upload(self):
        self.login(self.student)
        response = self.client.post(self.url, {
            'first_name': 'S', 'last_name': 'T', 'email': 'student@example.com',
            'picture': png_upload(),
        })
        self.assertEqual(response.status_code, 302)
        profile = ProfileImg.objects.get(user=self.student)
        self.assertTrue(profile.picture.name.startswith('profile_images/'))

    def test_non_image_upload_rejected(self):
        self.login(self.student)
        fake = SimpleUploadedFile('evil.png', b'<?php echo 1; ?>', content_type='image/png')
        response = self.client.post(self.url, {
            'first_name': 'Changed', 'last_name': 'T', 'email': 'student@example.com', 'picture': fake,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('picture', response.context['edit_profile_img_form'].errors)
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'S')

    def test_disallowed_extension_rejected(self):
        self.login(self.student)
        response = self.client.post(self.url, {
            'first_name': 'S', 'last_name': 'T', 'email': 'student@example.com',
            'picture': png_upload('avatar.svg'),
        })
        self.assertEqual(response.status_code, 400)

    def test_oversized_picture_rejected(self):
        self.login(self.student)
        with mock.patch('accounts.forms.PROFILE_IMAGE_MAX_MB', 0):
            response = self.client.post(self.url, {
                'first_name': 'S', 'last_name': 'T', 'email': 'student@example.com',
                'picture': png_upload(),
            })
        self.assertEqual(response.status_code, 400)

    def test_cannot_target_another_user(self):
        self.login(self.student)
        self.client.post(self.url, {
            'first_name': 'Hacked', 'last_name': 'X', 'email': 'student@example.com',
            'id': self.teacher.pk, 'user': self.teacher.pk, 'pk': self.teacher.pk,
        })
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.first_name, 'T')
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Hacked')

    def test_get_not_allowed_and_anonymous_redirected(self):
        self.assertEqual(self.client.post(self.url, {'email': 'a@b.com'}).status_code, 302)
        self.login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 405)


class NotificationTest(AuthedTestCase):

    def setUp(self):
        self.mine_old = notify(self.student, 'Old one')
        self.mine_new = notify(self.student, 'New one', link='/user_profile/', kind='success')
        self.theirs = notify(self.teacher, 'Teacher only')

    def test_list_returns_only_own_newest_first(self):
        self.login(self.student)
        data = self.client.get(reverse('notifications_list')).json()
        self.assertEqual(data['unread_count'], 2)
        ids = [n['id'] for n in data['notifications']]
        self.assertEqual(ids, [self.mine_new.id, self.mine_old.id])
        self.assertNotIn(self.theirs.id, ids)
        first = data['notifications'][0]
        self.assertEqual(first['message'], 'New one')
        self.assertFalse(first['is_read'])
        self.assertIn('created_at', first)

    def test_mark_one_read(self):
        self.login(self.student)
        response = self.client.post(reverse('notification_read', args=[self.mine_old.id]))
        self.assertEqual(response.json()['unread_count'], 1)
        self.mine_old.refresh_from_db()
        self.assertTrue(self.mine_old.is_read)

    def test_cannot_mark_someone_elses_read(self):
        self.login(self.student)
        response = self.client.post(reverse('notification_read', args=[self.theirs.id]))
        self.assertEqual(response.status_code, 404)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_read)

    def test_mark_all_read_only_affects_own(self):
        self.login(self.student)
        response = self.client.post(reverse('notifications_read_all'))
        self.assertEqual(response.json()['updated'], 2)
        self.assertFalse(Notification.objects.filter(user=self.student, is_read=False).exists())
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_read)

    def test_state_changes_require_post_and_login(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse('notification_read', args=[self.mine_old.id])).status_code, 405)
        self.assertEqual(self.client.get(reverse('notifications_read_all')).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('notifications_list')).status_code, 302)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        self.assertEqual(client.post(reverse('notifications_read_all')).status_code, 403)

    def test_header_shows_real_unread_count(self):
        self.login(self.student)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['notif_unread_count'], 2)
        self.assertContains(response, 'id="notifCount">2</span>', html=False)
        self.assertNotContains(response, '<span class="badge-count">5</span>')

    def test_header_hides_badge_when_no_unread(self):
        Notification.objects.filter(user=self.student).update(is_read=True)
        self.login(self.student)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'id="notifCount" hidden')

    def test_external_links_are_dropped(self):
        n = notify(self.student, 'x', link='https://evil.example.com/')
        self.assertEqual(n.link, '')

    def test_comment_notifies_course_teacher(self):
        course = Course.objects.create(
            student=self.teacher, title='Notify', category='python', level='beginner',
            Course_price=0, description='x', is_published=True,
        )
        self.login(self.student)
        self.client.post(reverse('add_comment', args=[course.id]), {'text': 'Great!'})
        self.assertTrue(Notification.objects.filter(user=self.teacher, message__contains='commented').exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PlaylistEditDeleteTest(TempMediaMixin, AuthedTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_teacher = make_user('teacher2@example.com', role='teacher')
        cls.course = Course.objects.create(
            student=cls.teacher, title='Mine', category='python', level='beginner',
            Course_price=0, description='x', is_published=True,
        )
        cls.other_course = Course.objects.create(
            student=cls.other_teacher, title='Theirs', category='python', level='beginner',
            Course_price=0, description='x', is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)

    def setUp(self):
        self.first = self.add(self.course, 'one.mp4', 1)
        self.second = self.add(self.course, 'two.mp4', 2)
        self.third = self.add(self.course, 'three.mp4', 3)
        self.foreign = self.add(self.other_course, 'foreign.mp4', 1)

    def add(self, course, name, order):
        return Playlist.objects.create(
            course=course, order=order,
            video=SimpleUploadedFile(name, b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4'),
        )

    def edit_url(self, course, entry):
        return reverse('edit_playlist_video', args=[course.id, entry.id])

    def delete_url(self, course, entry):
        return reverse('delete_playlist_video', args=[course.id, entry.id])

    def ordered_ids(self, course):
        return list(Playlist.objects.filter(course=course).values_list('id', flat=True))

    def test_owner_listing_has_manage_urls_student_does_not(self):
        self.login(self.teacher)
        data = self.client.get(reverse('get_playlist_videos', args=[self.course.id])).json()
        self.assertTrue(data['can_manage'])
        self.assertEqual([v['id'] for v in data['videos']], [self.first.id, self.second.id, self.third.id])
        self.assertIn('edit_url', data['videos'][0])
        self.login(self.student)
        data = self.client.get(reverse('get_playlist_videos', args=[self.course.id])).json()
        self.assertFalse(data['can_manage'])
        self.assertNotIn('edit_url', data['videos'][0])
        self.assertNotIn(self.foreign.id, [v['id'] for v in data['videos']])

    def test_edit_title_description_and_position(self):
        self.login(self.teacher)
        response = self.client.post(self.edit_url(self.course, self.third), {
            'title': ' Intro ', 'description': 'Start here', 'position': 1,
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['success'])
        self.third.refresh_from_db()
        self.assertEqual(self.third.title, 'Intro')
        self.assertEqual(self.third.description, 'Start here')
        self.assertEqual(self.ordered_ids(self.course), [self.third.id, self.first.id, self.second.id])
        self.assertEqual(
            list(Playlist.objects.filter(course=self.course).values_list('order', flat=True)), [1, 2, 3],
        )
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.order, 1)

    def test_blank_title_falls_back_to_file_name(self):
        self.login(self.teacher)
        self.client.post(self.edit_url(self.course, self.first), {'title': '', 'position': 1})
        self.first.refresh_from_db()
        self.assertTrue(self.first.display_title.startswith('one'))

    def test_replace_video_removes_old_file(self):
        self.login(self.teacher)
        old_path = self.first.video.path
        response = self.client.post(self.edit_url(self.course, self.first), {
            'position': 1,
            'video': SimpleUploadedFile('new.webm', b'webm', content_type='video/webm'),
        })
        self.assertEqual(response.status_code, 200)
        self.first.refresh_from_db()
        self.assertIn('new', self.first.video.name)
        self.assertFalse(os.path.exists(old_path))

    def test_invalid_input_rejected(self):
        self.login(self.teacher)
        cases = [
            {'title': 'x' * 201, 'position': 1},
            {'title': 'ok', 'position': 0},
            {'title': 'ok', 'position': 'abc'},
            {'title': 'ok', 'position': 1,
             'video': SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')},
        ]
        for data in cases:
            response = self.client.post(self.edit_url(self.course, self.first), data)
            self.assertEqual(response.status_code, 400, data)
            self.assertTrue(response.json()['errors'])
        self.first.refresh_from_db()
        self.assertEqual(self.first.title, '')

    def test_cross_course_ids_are_404(self):
        self.login(self.teacher)
        # Teacher's own course id in the URL, but another course's entry.
        response = self.client.post(self.edit_url(self.course, self.foreign), {'title': 'Hijack', 'position': 1})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(self.delete_url(self.course, self.foreign))
        self.assertEqual(response.status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, '')
        self.assertTrue(Playlist.objects.filter(pk=self.foreign.pk).exists())

    def test_other_teacher_and_student_forbidden(self):
        for user in (self.other_teacher, self.student):
            self.login(user)
            response = self.client.post(self.edit_url(self.course, self.first), {'title': 'X', 'position': 1})
            self.assertEqual(response.status_code, 403)
            response = self.client.post(self.delete_url(self.course, self.first))
            self.assertEqual(response.status_code, 403)
        self.first.refresh_from_db()
        self.assertEqual(self.first.title, '')
        self.assertEqual(Playlist.objects.filter(course=self.course).count(), 3)

    def test_superuser_can_manage(self):
        self.login(self.superuser)
        response = self.client.post(self.edit_url(self.course, self.first), {'title': 'Admin fix', 'position': 1})
        self.assertEqual(response.status_code, 200)

    def test_delete_removes_entry_and_file_and_renumbers(self):
        self.login(self.teacher)
        path = self.first.video.path
        response = self.client.post(self.delete_url(self.course, self.first))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['remaining'], 2)
        self.assertFalse(Playlist.objects.filter(pk=self.first.pk).exists())
        self.assertFalse(os.path.exists(path))
        self.assertEqual(self.ordered_ids(self.course), [self.second.id, self.third.id])
        self.assertEqual(
            list(Playlist.objects.filter(course=self.course).values_list('order', flat=True)), [1, 2],
        )
        self.assertTrue(Playlist.objects.filter(pk=self.foreign.pk).exists())

    def test_get_and_anonymous_rejected(self):
        self.login(self.teacher)
        self.assertEqual(self.client.get(self.delete_url(self.course, self.first)).status_code, 405)
        self.assertEqual(self.client.get(self.edit_url(self.course, self.first)).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(self.delete_url(self.course, self.first)).status_code, 302)
        self.assertTrue(Playlist.objects.filter(pk=self.first.pk).exists())

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.teacher)
        self.assertEqual(client.post(self.delete_url(self.course, self.first)).status_code, 403)
        self.assertTrue(Playlist.objects.filter(pk=self.first.pk).exists())

    def test_new_upload_goes_last_and_notifies_students(self):
        self.login(self.teacher)
        response = self.client.post(reverse('add_playlist', args=[self.course.id]), {
            'video': SimpleUploadedFile('four.mp4', b'\x00', content_type='video/mp4'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ordered_ids(self.course)[-1], response.json()['video']['id'])
        self.assertTrue(Notification.objects.filter(user=self.student, message__contains='New video').exists())
        self.assertFalse(Notification.objects.filter(user=self.other_teacher).exists())


class NotificationTriggerTest(AuthedTestCase):
    """Real application events create notifications for the right people."""

    def test_teacher_application_approve_and_reject(self):
        from teacher.models import TeacherApplication
        app = TeacherApplication.objects.create(
            user=self.student, experience='3', expertise='programming',
            c_v='teacher_cv/cv.pdf', reason='Love teaching',
        )
        self.login(self.superuser)
        self.client.get(reverse('approve_staff', args=[app.pk]))
        self.assertTrue(Notification.objects.filter(
            user=self.student, kind='success', message__contains='approved').exists())
        self.client.get(reverse('reject_staff', args=[app.pk]))
        self.assertTrue(Notification.objects.filter(
            user=self.student, kind='warning').exists())
        self.assertFalse(Notification.objects.filter(user=self.superuser).exists())

    def test_paid_enrollment_notifies_student_and_teacher_once(self):
        from student.payments import simulate_hesabpay_success
        course = Course.objects.create(
            student=self.teacher, title='Paid', category='python', level='beginner',
            Course_price=5, description='x', is_published=True,
        )
        order = CourseOrder.objects.create(student=self.student, course=course)
        with self.captureOnCommitCallbacks(execute=True):
            simulate_hesabpay_success(order)
        self.assertEqual(Notification.objects.filter(user=self.student, message__contains='enrolled').count(), 1)
        self.assertEqual(Notification.objects.filter(user=self.teacher, message__contains='enrolled').count(), 1)
