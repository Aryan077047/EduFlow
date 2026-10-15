"""Give every user's pre-conversation AI messages their own sidebar chat.

The AI assistant used to store one flat stream of messages per user
(AIChatMessage.conversation being NULL). This migration moves each user's
orphan messages into a new AIConversation titled "Old chat" so the sidebar
shows their existing history too.
"""
from django.db import migrations


def group_orphans(apps, schema_editor):
    AIConversation = apps.get_model('accounts', 'AIConversation')
    AIChatMessage = apps.get_model('accounts', 'AIChatMessage')

    orphan_user_ids = (
        AIChatMessage.objects.filter(conversation__isnull=True)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in orphan_user_ids:
        conv = AIConversation.objects.create(user_id=user_id, title='Old chat')
        AIChatMessage.objects.filter(
            user_id=user_id, conversation__isnull=True,
        ).update(conversation=conv)


def ungroup(apps, schema_editor):
    AIChatMessage = apps.get_model('accounts', 'AIChatMessage')
    AIConversation = apps.get_model('accounts', 'AIConversation')
    AIChatMessage.objects.filter(
        conversation__title='Old chat').update(conversation=None)
    AIConversation.objects.filter(title='Old chat').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_aiconversation_aichatmessage_conversation'),
    ]

    operations = [
        migrations.RunPython(group_orphans, ungroup),
    ]
