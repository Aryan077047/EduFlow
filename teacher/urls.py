from django.urls import path

from . import views

urlpatterns = [
    # ============ COURSES ============
    path('prof_course/', views.prof_course, name='prof_course'),
    path('publish_course/<int:course_id>/', views.publish_course, name='publish_course'),
    path('delet_course/<int:id>/', views.delet_course, name='delet_course'),
    path('course/<int:course_id>/lessons/', views.course_lessons, name='course_lessons'),
    path('add_playlist/<int:course_id>/', views.add_playlist, name='add_playlist'),
    path('get_playlist_videos/<int:course_id>/', views.get_playlist_videos, name='get_playlist_videos'),

    # ============ TEACHER APPLICATION ============
    path('apply_teacher/', views.apply_teacher, name='apply_teacher'),

    # ============ TEACHER ANALYTICS ============
    path('teacher_analytics/', views.teacher_analytics, name='teacher_analytics'),
    path('teacher_analytics/export/', views.teacher_analytics_csv, name='teacher_analytics_csv'),

    # ============ QUIZ ROUTES (builder + grading) ============
    path('quiz/', views.quiz, name='quiz'),
    path('save_quiz/', views.save_quiz, name='save_quiz'),
    path('quiz/publish/<int:quiz_id>/', views.publish_quiz, name='publish_quiz'),
    path('quiz/<int:quiz_id>/submissions/', views.quiz_submissions, name='quiz_submissions'),
    path('attempt_detail/<int:attempt_id>/', views.attempt_detail, name='attempt_detail'),
    path('quiz/attempt/<int:attempt_id>/grade/', views.grade_attempt, name='grade_attempt'),
    path('grade_attempt/', views.grade_attempt, name='grade_attempt_legacy'),
]
