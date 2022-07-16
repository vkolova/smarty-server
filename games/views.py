from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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

from django.core.cache import cache


class GameView(mixins.CreateModelMixin,
            mixins.RetrieveModelMixin,
            mixins.UpdateModelMixin,
            mixins.DestroyModelMixin,
            mixins.ListModelMixin,
            viewsets.GenericViewSet):
    
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def get_random_player(self):
        players = Player.objects.exclude(pk=self.request.user.id).exclude(push_notification_token__isnull=True)
        count = players.count()
        slice = random.random() * (count - 1)
        player = players[slice: slice+1][0]
        return player
    

    def perform_create(self, serializer):
        opponentUsername = self.request.data.get('username', None)

        if opponentUsername:
            opponent = Player.objects.get(user__username=opponentUsername)
        else:
            opponent = self.get_random_player()

        creator = Player.objects.get(pk=self.request.user.id)
        players = Player.objects.filter(pk__in=(self.request.user.id, opponent.id))

        serializer.save(players=players)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'online_users',
            {
                'type': 'game_invitation',
                'data': {
                    'invited': opponent.user.username,
                    'invited_by': SimplePlayerSerializer().to_representation(creator),
                    'channel': serializer.data['channel']
                }
            }
        )
