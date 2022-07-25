from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import mixins, viewsets
from rest_framework.exceptions import APIException

import random

from players.models import Player
from players.serializers import  SimplePlayerSerializer

from .models import Game
from .serializers import GameSerializer

from django.core.cache import cache

class NoPlayerSpecified(APIException):
    status_code = 400
    default_detail = 'No player specified.'
    default_code = 'bad_request'


class GameView(mixins.CreateModelMixin,
            mixins.RetrieveModelMixin,
            mixins.UpdateModelMixin,
            mixins.DestroyModelMixin,
            mixins.ListModelMixin,
            viewsets.GenericViewSet):
    
    queryset = Game.objects.all()
    serializer_class = GameSerializer    

    def perform_create(self, serializer):
        opponentUsername = self.request.data.get('username', None)

        if opponentUsername:
            opponent = Player.objects.get(user__username=opponentUsername)
        else:
            raise NoPlayerSpecified

        creator = Player.objects.get(user=self.request.user)
        players = Player.objects.filter(user__in=(self.request.user, opponent.user))

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
