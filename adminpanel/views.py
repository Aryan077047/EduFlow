import csv
from datetime import timedelta

from django.shortcuts import render, redirect
from django.conf import settings  # noqa: F401  (kept for parity with other apps)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Count
from django.utils import timezone

from accounts.models import AIChatMessage, PasswordResetOTP
from teacher.models import Course, Lesson, Playlist, Quiz, TeacherApplication
from student.models import Comment, Enrollment, Like, Post, QuizAttempt

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
    total_enrollments = Enrollment.objects.count()
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
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponseForbidden

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
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponseForbidden

    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser only")

    application = get_object_or_404(TeacherApplication, pk=pk)
    application.status = 'rejected'
    application.save()

    return redirect('admin_dashboard')


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
    from teacher.models import Lesson

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
