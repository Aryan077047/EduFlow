from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admmitions', '0005_quizattempt_studentanswer'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_published',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='course',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
