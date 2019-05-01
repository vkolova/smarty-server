from django.contrib import admin
from .models import Game, Round

class RoundAdmin(admin.ModelAdmin):
    model = Round
    fields = ('id', 'winner', 'question')
    list_display = ('id', 'winner', 'question_text')
    ordering = ('-id',)

    def question_text(self, obj):
        return obj.question.content



class GameAdmin(admin.ModelAdmin):
    model = Game
    fields = ('id', 'channel', 'players', 'winner', 'state', 'data')
    list_display = ('id', 'channel', 'winner',)
    readonly_fields = ('id', 'channel',)
    ordering = ('-id',)

admin.site.register(Game, GameAdmin)
admin.site.register(Round, RoundAdmin)