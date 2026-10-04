import json
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import (
    User, Course, Enrollment, Quiz, Playlist,
)


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
        self.login(self.student)
        response = self.client.post(
            reverse('enroll_course', args=[self.published.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
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
