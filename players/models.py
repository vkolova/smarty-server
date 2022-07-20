from django.conf import settings

from django.db import models
from django.db.models.signals import post_save

from django.dispatch import receiver


class Player(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        parent_link=False,
        on_delete=models.CASCADE,
        related_name='player'
    )
    score = models.BigIntegerField(
        default=0,
        help_text='Player points'
    )
    avatar = models.TextField(
        max_length=500, 
        help_text='Avatar url'
    )
    push_notification_token = models.CharField(
        max_length=50,
        help_text='Expo push notification token',
        blank=True,
        null=True,
        default=None
    )
