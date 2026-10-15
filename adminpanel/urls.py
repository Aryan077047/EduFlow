from django.urls import path

from . import views

urlpatterns = [
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),

    # ============ STAFF ============
    path('approve-staff/<int:pk>/', views.approve_staff, name='approve_staff'),
    path('reject-staff/<int:pk>/', views.reject_staff, name='reject_staff'),

    # ============ ADMIN ANALYTICS ============
    path('admin_analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin_analytics/export/', views.admin_analytics_csv, name='admin_analytics_csv'),
]
