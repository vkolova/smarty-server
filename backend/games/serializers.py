from rest_framework import serializers

from players.serializers import UserSerializer, SimplePlayerSerializer
from questions.serializers import QuestionSerializer
from .models import Game, Round


class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ('id', 'player_a_time', 'player_b_time', 'winner', 'question')
        write_once_fields = ('winner',)
    
        player_a_time = serializers.DateTimeField(required=False)
        player_b_time = serializers.DateTimeField(required=False)


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'channel', 'players', 'state', 'created', 'finished', 'winner', 'rounds', 'data')
        read_only_fields = ('id', 'channel', 'created')
        write_once_fields = ('channel')

    channel = serializers.UUIDField(format='hex_verbose', required=False)
    players = SimplePlayerSerializer(many=True, required=False)

    state = serializers.CharField(max_length=15, allow_blank=False, required=False)
    created = serializers.DateTimeField(required=False)
    finished = serializers.DateTimeField(required=False)
    winner = SimplePlayerSerializer(required=False)
    data = serializers.JSONField(required=False)

    rounds = RoundSerializer(many=True, required=False)
        
