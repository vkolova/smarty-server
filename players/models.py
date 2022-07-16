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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_player_profile(sender, instance, created, **kwargs):
    if created:
        player_profile = Player.objects.create(user=instance, avatar='http://prikachi.com/images/569/9566569j.png')
        player_profile.save()
