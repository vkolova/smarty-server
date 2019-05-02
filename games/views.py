from django.shortcuts import render
from rest_framework import serializers, mixins, permissions, viewsets, status, generics
from rest_framework.response import Response
from exponent_server_sdk import PushMessage
import random

from players.models import Player
from players.serializers import PlayerSerializer, SimplePlayerSerializer
from players.notifications import send_push_message
from questions.models import Question

from .models import Game
from .serializers import GameSerializer


class GameView(mixins.CreateModelMixin,
            mixins.RetrieveModelMixin,
            mixins.UpdateModelMixin,
            mixins.DestroyModelMixin,
            mixins.ListModelMixin,
            viewsets.GenericViewSet):
    
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def get_random_player(self):
        players = Players.objects.exclude(pk=self.request.user.id)
        count = players.count()
        slice = random.random() * (count - 1)
        player = players[slice: slice+1][0]
        return player

    def perform_create(self, serializer):
        opponent = self.request.data.get('opponent', None)
        ids = (self.request.user.id, opponent) if opponent else (self.request.user.id, self.get_random_player())
        
        creator = Player.objects.get(pk=self.request.user.id)
        opponent = Player.objects.get(pk=opponent)
        players = Player.objects.filter(pk__in=ids)

        serializer.save(players=players)
    
        send_push_message(PushMessage(
            to=opponent.push_notification_token,
            title='Покана за игра',
            body='Поканиха Ви за игра',
            priority='high',
            channel_id='game_invite',
            data={
                'invited_by': SimplePlayerSerializer().to_representation(creator),
                'channel': serializer.instance.channel.hex
            }
        ))
    