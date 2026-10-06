from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register_teacher', views.register_teacher, name='register_teacher'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('user_login', views.user_login, name='user_login'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('user_logout', views.user_logout, name='user_logout'),
    path('prof_course/', views.prof_course, name='prof_course'),
    path('delet_course/<int:id>/', views.delet_course, name='delet_course'),
    path('priview/<int:id>/', views.priview, name='priview'),
    path('apply_teacher/', views.apply_teacher, name='apply_teacher'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('profile_img_view/', views.profile_img_view, name='profile_img_view'),
    path('enroll_course/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('add_playlist/<int:course_id>/', views.add_playlist, name='add_playlist'),
    path('get_playlist_videos/<int:course_id>/', views.get_playlist_videos, name='get_playlist_videos'),
    path('course/<int:course_id>/lessons/', views.course_lessons, name='course_lessons'),

    # Comments & Likes
    path('add-comment/<int:course_id>/', views.add_comment, name='add_comment'),
    path('remove-comment/<int:comment_id>/', views.remove_comment, name='remove_comment'),
    path('like-course/<int:course_id>/', views.like_course, name='like_course'),
    path('get-like-status/<int:course_id>/', views.get_like_status, name='get_like_status'),

    # Staff
    path('approve-staff/<int:pk>/', views.approve_staff, name='approve_staff'),
    path('reject-staff/<int:pk>/', views.reject_staff, name='reject_staff'),
    path('setting/', views.setting, name='setting'),

    # ============ QUIZ ROUTES ============
    path('quiz/', views.quiz, name='quiz'),                              # quiz builder page
    path('save_quiz/', views.save_quiz, name='save_quiz'),
    path('submit_quiz/', views.submit_quiz, name='submit_quiz'),
    path('quiz/publish/<int:quiz_id>/', views.publish_quiz, name='publish_quiz'),
    path('take_quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'), # student takes a quiz

    # ✅ single, clean submissions URL (with leading "quiz/" prefix)
    path('quiz/<int:quiz_id>/submissions/', views.quiz_submissions, name='quiz_submissions'),

    path('quiz_result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('attempt_detail/<int:attempt_id>/', views.attempt_detail, name='attempt_detail'),
    path('quiz/attempt/<int:attempt_id>/grade/', views.grade_attempt, name='grade_attempt'),
    path('grade_attempt/', views.grade_attempt, name='grade_attempt_legacy'),
    path('publish_course/<int:course_id>/', views.publish_course, name='publish_course'),

    # ============ AI STUDY ASSISTANT ============
    path('ai_assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai_assistant/ask/', views.ask_ai, name='ask_ai'),
    path('ai_assistant/clear/', views.clear_ai_chat, name='clear_ai_chat'),

    # ============ ADMIN ANALYTICS ============
    path('admin_analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin_analytics/export/', views.admin_analytics_csv, name='admin_analytics_csv'),

    # ============ TEACHER ANALYTICS ============
    path('teacher_analytics/', views.teacher_analytics, name='teacher_analytics'),
    path('teacher_analytics/export/', views.teacher_analytics_csv, name='teacher_analytics_csv'),
]
