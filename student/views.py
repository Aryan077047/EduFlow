import json

import hesabpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Comment, CourseOrder, Enrollment, Like, QuizAttempt, StudentAnswer
from teacher.models import Course, Quiz, Question, Answer
from accounts.models import ProfileImg


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

    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).first()
    if enrollment:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'info',
                'message': 'You are already enrolled in this course.'
            })

        messages.info(request, "You are already enrolled in this course.")
        return redirect("user_profile")

    order = CourseOrder.objects.create(student=request.user, course=course)
    try:
        session = hesabpay.checkout(
            order,
            user=request.user,
            request=request,
            items=[{
                'id': str(course.id),
                'name': course.title,
                'price': float(course.Course_price),
            }],
        )
    except hesabpay.exceptions.HesabPayError as exc:
        order.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'error': f'Payment service error: {exc}',
            }, status=500)
        messages.error(request, 'Payment service is temporarily unavailable. Please try again later.')
        return redirect('index')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'checkout',
            'checkout_url': session.url,
        })

    return redirect(session.url)


@login_required
def payment_success(request):
    return render(request, 'payment_success.html')


@login_required
def payment_failure(request):
    return render(request, 'payment_failure.html')


@login_required
@require_POST
def add_comment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    text = request.POST.get('text', '').strip()

    if not text:
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
        except Exception:
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
    course = quiz_obj.course

    is_quiz_author = (quiz_obj.teacher == request.user)
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
        data = json.loads(request.body)
        quiz_id = data.get('quiz_id')
        answers = data.get('answers', [])

        if not quiz_id:
            return JsonResponse(
                {'status': 'error', 'message': 'Missing quiz_id.'},
                status=400
            )

        quiz_obj = get_object_or_404(Quiz, id=quiz_id)
        course = quiz_obj.course

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

        total_auto_score = 0
        has_manual_question = False

        for question in quiz_obj.questions.all():
            sub = answer_map.get(question.id, {})

            if question.question_type == 'mc':
                selected_id = sub.get('answer_id')
                selected = None
                is_correct = False

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
            attempt.status = 'graded'
            attempt.graded_at = timezone.now()
        attempt.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Quiz submitted successfully!',
            'attempt_id': attempt.id,
            'score': attempt.total_score,
            'percentage': attempt.percentage,
            'needs_grading': has_manual_question,
            'redirect_url': reverse('quiz_result', kwargs={'attempt_id': attempt.id}),
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
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    is_owner = (attempt.student == request.user)
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
        'attempt': attempt,
        'quiz': attempt.quiz,
        'answers': answers,
        'is_teacher_view': is_teacher and not is_owner,
    }
    return render(request, 'quiz_result.html', context)
