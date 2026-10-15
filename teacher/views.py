import json
import os
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import TeacherApplicationForm, course_form
from .models import (
    Course,
    Lesson,
    Playlist,
    Quiz,
    Question,
    Answer,
    TeacherApplication,
)
from accounts.models import User, ProfileImg
from accounts.views import _profile_page_context
from student.models import Comment, Enrollment, Like, QuizAttempt, StudentAnswer


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


@login_required
@require_POST
def delet_course(request, id):
    course_ = get_object_or_404(Course, id=id, student=request.user)
    title = course_.title
    course_.delete()
    messages.success(request, f'Course "{title}" deleted.')
    return redirect('user_profile')


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
            video_url = playlist.video.url if playlist.video else ''
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

    total = attempts.count()
    submitted = attempts.filter(status='submitted').count()
    graded = attempts.filter(status='graded').count()
    passed = sum(1 for a in attempts if a.status == 'graded' and a.passed)

    context = {
        'quiz': quiz_obj,
        'course': quiz_obj.course,
        'attempts': attempts,
        'stats': {
            'total': total,
            'submitted': submitted,
            'graded': graded,
            'passed': passed,
        },
    }
    return render(request, 'quiz_submission.html', context)


@login_required
def attempt_detail(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
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
        'quiz': quiz_obj,
        'course': quiz_obj.course,
        'answers': answers,
    }
    return render(request, 'attempt_details.html', context)


@login_required
@require_POST
def grade_attempt(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
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
        ans.points_awarded = pts
        ans.teacher_feedback = g.get('feedback', '')
        ans.is_correct = (pts >= ans.question.points)
        ans.graded_at = timezone.now()
        ans.save()

    attempt.manual_score = sum(
        a.points_awarded
        for a in attempt.answers.filter(question__question_type='explain')
    )
    attempt.status = 'graded'
    attempt.graded_by = request.user
    attempt.graded_at = timezone.now()
    attempt.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Grades saved.',
        'total_score': attempt.total_score,
        'percentage': attempt.percentage,
    })


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


# ============================================================
# TEACHER — MY DATA ANALYSIS REPORT (scoped to one teacher)
# ============================================================

def _growth_pct(current, previous):
    """Signed percentage change, tolerant of a zero baseline."""
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


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
    import csv

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
