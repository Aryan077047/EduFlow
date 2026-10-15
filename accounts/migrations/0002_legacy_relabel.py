"""Repoint bookkeeping rows at the new app labels after the split.

The models kept their original database tables (db_table='admmitions_*'),
so no table or row data changes here. We only fix:

1. django_content_type rows (app_label='admmitions') -> new app labels,
   so generic relations (e.g. hesabpay HesabPayPayment.content_type)
   keep resolving after the old app is gone, and get_for_model() cannot
   create duplicate rows.
2. django_migrations rows recorded for the removed 'admmitions' app.

Both statements are no-ops on a fresh database.
"""
from django.db import migrations

# legacy model (lowercase) -> new app label
MODEL_APP_MAP = {
    'user': 'accounts',
    'profileimg': 'accounts',
    'passwordresetotp': 'accounts',
    'aichatmessage': 'accounts',
    'course': 'teacher',
    'playlist': 'teacher',
    'lesson': 'teacher',
    'quiz': 'teacher',
    'question': 'teacher',
    'answer': 'teacher',
    'teacherapplication': 'teacher',
    'enrollment': 'student',
    'courseorder': 'student',
    'post': 'student',
    'comment': 'student',
    'like': 'student',
    'quizattempt': 'student',
    'studentanswer': 'student',
}


def relabel_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for legacy_model, new_app in MODEL_APP_MAP.items():
        ContentType.objects.filter(
            app_label='admmitions', model=legacy_model,
        ).update(app_label=new_app)


def revert_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for legacy_model, new_app in MODEL_APP_MAP.items():
        ContentType.objects.filter(
            app_label=new_app, model=legacy_model,
        ).update(app_label='admmitions')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('teacher', '0001_initial'),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(relabel_content_types, revert_content_types),
        migrations.RunSQL(
            "DELETE FROM django_migrations WHERE app = 'admmitions'",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
