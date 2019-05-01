from django.contrib import admin
from .models import Game

class GameAdmin(admin.ModelAdmin):
    model = Game
    fields = ('id', 'channel', 'players', 'winner', 'state', 'data')
    list_display = ('id', 'channel', 'winner',)
    readonly_fields = ('id', 'channel',)
    ordering = ('-id',)

admin.site.register(Game, GameAdmin)