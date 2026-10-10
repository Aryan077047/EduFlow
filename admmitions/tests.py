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

from .models import (
    User, Course, Enrollment, Quiz, Playlist, PasswordResetOTP, AIChatMessage,
    CourseOrder,
    Comment, Like, QuizAttempt, Question,
)
from .views import _build_analytics, _build_teacher_analytics
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
        from admmitions.payments import simulate_hesabpay_success
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
        with override_settings(EMAIL_BACKEND='admmitions.tests.ExplodingEmailBackend'):
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

    def ask(self, question='What is a loop?', course_id=None):
        return self.client.post(
            reverse('ask_ai'),
            data=json.dumps({'question': question, 'course_id': course_id}),
            content_type='application/json',
        )

    def patched_deepseek(self, reply='A loop repeats instructions.'):
        return mock.patch(
            'admmitions.views._call_deepseek', return_value=reply,
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
        # The course mention turn must not be injected for a non-existent id.
        sent = deepseek.call_args[0][0]
        self.assertEqual(len(sent), 2)  # context + question only

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
            'admmitions.views._call_deepseek',
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
            'admmitions.views._call_deepseek',
            side_effect=HTTPError('url', 404, 'Not Found', hdrs=None, fp=None),
        ):
            response = self.ask()
        self.assertEqual(response.status_code, 502)
        self.assertIn('unavailable', response.json()['error'])


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
