from django.contrib import admin
from .models import TeacherApplication

    
    
@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'expertise', 'experience', 'status')

    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        for app in queryset:
            app.status = 'approved'
            app.save()

          
            app.user.role = 'teacher'
            app.user.save()

    approve_selected.short_description = "Approve selected applications"

    def reject_selected(self, request, queryset):
        for app in queryset:
            app.status = 'rejected'
            app.save()

    
            app.user.role = 'student'
            app.user.save()

    reject_selected.short_description = "Reject selected applications"