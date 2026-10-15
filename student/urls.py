from django.urls import path

from . import views

urlpatterns = [
    # ============ ENROLLMENT / PAYMENTS ============
    path('enroll_course/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('payments/success/', views.payment_success, name='payment_success'),
    path('payments/failure/', views.payment_failure, name='payment_failure'),

    # ============ COMMENTS & LIKES ============
    path('add-comment/<int:course_id>/', views.add_comment, name='add_comment'),
    path('remove-comment/<int:comment_id>/', views.remove_comment, name='remove_comment'),
    path('like-course/<int:course_id>/', views.like_course, name='like_course'),
    path('get-like-status/<int:course_id>/', views.get_like_status, name='get_like_status'),

    # ============ QUIZ ROUTES (taking) ============
    path('take_quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('submit_quiz/', views.submit_quiz, name='submit_quiz'),
    path('quiz_result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
]
