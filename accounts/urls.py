from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user_login', views.user_login, name='user_login'),
    path('register_teacher', views.register_teacher, name='register_teacher'),
    path('user_logout', views.user_logout, name='user_logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('priview/<int:id>/', views.priview, name='priview'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('profile_img_view/', views.profile_img_view, name='profile_img_view'),
    path('setting/', views.setting, name='setting'),
    path('setting/language/', views.save_language, name='save_language'),
    path('setting/change_password/', views.change_password, name='change_password'),
    path('setting/delete_account/', views.delete_account, name='delete_account'),

    # ============ AI STUDY ASSISTANT ============
    path('ai_assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai_assistant/ask/', views.ask_ai, name='ask_ai'),
    path('ai_assistant/clear/', views.clear_ai_chat, name='clear_ai_chat'),
    path('ai_assistant/chat/delete/', views.delete_ai_conversation, name='delete_ai_conversation'),
]
