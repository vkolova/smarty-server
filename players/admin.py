from django.contrib import admin

from .models import Player

class PlayerAdmin(admin.ModelAdmin):
    model = Player
    fields = ('id', 'user', 'score', 'avatar', 'games', 'push_notification_token',)
    list_display = ('id', 'user', 'score', 'level', 'push_notification_token')
    readonly_fields = ('id', 'user', 'level', 'games')
    ordering = ('-id',)

    def games(self, obj):
        return obj.games

    def level(self, obj):
        return 1


admin.site.register(Player, PlayerAdmin)