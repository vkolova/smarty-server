from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import mixins, viewsets


import random

from players.models import Player
from players.serializers import  SimplePlayerSerializer

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
        players = Player.objects.exclude(user=self.request.user).exclude(push_notification_token__isnull=True)
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

        creator = Player.objects.get(user=self.request.user)
        players = Player.objects.filter(user__in=(self.request.user, opponent))

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
