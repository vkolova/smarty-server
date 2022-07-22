from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

from django.urls import include, re_path
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import transaction

from time import sleep
import json
import random

from games.models import Game, Round, GameState
from games.serializers import GameSerializer
from players.models import Player
from questions.models import Question
from questions.serializers import QuestionSerializer

GAME_ROUNDS_COUNT = 5
QUESTION_POINTS = 10

@database_sync_to_async
def get_user(token):
    try:
        token = Token.objects.get(key=token)
        return token.user
    except User.DoesNotExist:
        return AnonymousUser()

class QueryAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token = scope['url_route']['kwargs']['user_token']
        scope['user'] = await get_user(token)
        return await self.inner(scope, receive, send)


class GameConsumer(WebsocketConsumer):
    @property
    def game(self):
        game = Game.objects.get(channel=self.room_name)
        return game
    
    def players_obj(self, value):
        game = self.game
        data = {}
        for p in game.players.values():
            user = User.objects.get(pk=p['id'])
            data[user] = value
        return data
    
    def initialize_game_data(self):
        data = {
            'connected': [ self.user.username ],
            'score': self.players_obj(0)
        }
        return data
    
    def init_player_round_data(self, username):
        player_data = {
            'username': username,
            'timestamp': None,
            'is_correct': None,
            'answered': None
        }
        return player_data
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.user = self.scope['user']

        if self.user:
            self.accept()
            # Join room group
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.send_game_update()
        else:
            self.close()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data = text_data_json['data']
        type = text_data_json['type']
    
        if type == 'game_connect':
            self.game_connect(text_data_json)
        if type == 'question_answer':
            self.question_answer(text_data_json)

    ## GAME METHODS
    def start_game(self):
        game = self.game
        if game.state != 'in_progress' and game.state != 'finished':
            game.state = 'in_progress'
            game.save()
            sleep(0.3)
            self.send_game_update()
            self.new_round()
        else:
            self.send_question_update()

        self.send_game_update()
        self.send_score_update()

    def save_connected(self):
        self.game.refresh_from_db()
        game = self.game

        if not game.data:
            game.data = self.initialize_game_data()
        else:
            connected = game.data['connected']
            connected.append(self.user.username)
            game.data = {
                **game.data,
                'connected': list(set(connected))
            }
        game.save()
        self.send(text_data=json.dumps({
            'type': 'notification',
            'data': 'Welcome, %s' % self.user.username
        }))
    
    def check_all_connected(self):
        game = self.game

        if len(game.data['connected']) == 0:
            return False

        for u in game.players.values():
            if u['username'] not in game.data['connected']:
                return False
        return True

    def game_connect(self, event):
        game = self.game
        data = event['data']

        if data == 'ok':
            self.save_connected()
            players_are_connected = self.check_all_connected()

            if self.check_all_connected():
                self.start_game()
        else:
            game.state = GameState.DECLINED
            game.finished = datetime.now()
            game.save()
        self.send_game_update()

    def get_current_round(self):
        current_round = self.game.rounds.order_by('-id')[0]
        return current_round

    def initialize_next_round(self):
        self.new_round()
        self.send_score_update()
        self.send_game_update()
    
    def get_question(self):
        game = self.game
        questions_so_far = [r.question.pk for r in game.rounds.all()]
        available_questions = Question.objects.exclude(pk__in=questions_so_far)
        count = available_questions.count()
        slice = random.randint(0, count - 1)
        question = available_questions[slice: slice+1][0]
        return question

    def is_score_a_tie(self):
        game = self.game
        score_data = game.data['score']
        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']
        return score_data[player_a] == score_data[player_b]

    def check_game_end(self):
        game = self.game

        rounds_count = len(game.rounds.all())
        is_a_tie = self.is_score_a_tie()
        return rounds_count >= GAME_ROUNDS_COUNT and not is_a_tie

    def finish_game(self):
        game = self.game
        if game.finished:
            return
        
        score_data = game.data['score']
        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']

        p_a = Player.objects.get(username=player_a)
        p_a.score = p_a.score + score_data[player_a]
        p_a.save()
        
        p_b = Player.objects.get(username=player_b)
        p_b.score = p_b.score + score_data[player_b]
        p_b.save()

        game.winner = p_a if score_data[player_a] > score_data[player_b] else p_b
        game.state = GameState.FINISHED
        game.finished = datetime.now()
        game.save()

    def new_round(self):
        game = self.game
        players = game.data['connected']
        question = self.get_question()
        new_round = Round.objects.create(
            game=game, 
            question=question, 
            player_a={**self.init_player_round_data(players[0])},
            player_b={**self.init_player_round_data(players[1])}
        )
        self.send_question_update()
    

    def save_round_answer(self, data):
        with transaction.atomic():
            game = Game.objects.select_for_update().get(channel=self.room_name)
            current_round = game.rounds.order_by('-id').first()
            
            if current_round.player_a['username'] == self.user.username:
                current_round.player_a = {
                    **current_round.player_a,
                    **data
                }
            else: 
                current_round.player_b = {
                    **current_round.player_b,
                    **data
                }
            current_round.save()

    
    def check_all_answered(self):
        current_round = self.get_current_round()
        return True \
            if current_round.player_a['timestamp'] and current_round.player_b['timestamp'] \
            else False


    def select_round_winner(self):
        current_round = self.get_current_round()
        if current_round.finished:
            return

        player_a = current_round.player_a
        player_b = current_round.player_b

        if player_a['is_correct'] and player_b['is_correct']:
            winner = player_a['username'] if player_a['timestamp'] > player_b['timestamp'] else player_b['username']
        elif player_a['is_correct'] and not player_b['is_correct']:
            winner = player_a['username']
        elif not player_a['is_correct'] and player_b['is_correct']:
            winner = player_b['username']
        else:
            winner = None

        if winner:
            game = self.game
            game.data['score'][winner] = game.data['score'][winner] + QUESTION_POINTS
            game.save()
            current_round.winner = Player.objects.get(username=winner)
            current_round.finished = True
            current_round.save()

    def question_answer(self, event):
        data = event['data']
        user = self.user.username
        current_round = self.get_current_round()
        if current_round.finished:
            return

        is_correct = True if data['answer'] == current_round.question.correct_answer() else False
        self.save_round_answer({
            'timestamp': data['time'],
            'is_correct': is_correct,
            'answered': data['answer']
        })

        if self.check_all_answered():
            self.select_round_winner()
            self.send_round_winner()

            if self.check_game_end():
                self.finish_game()
                self.send_game_update()
            else:
                self.send_round_winner()
                self.initialize_next_round()

    ## GROUP METHODS
    def send_game_update(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_update',
                'data': GameSerializer().to_representation(self.game)
            }
        )
    
    def send_score_update(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'scores_update',
                'data': self.game.data['score']
            }
        )


    def send_question_update(self):
        current_round = self.get_current_round()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'question_update',
                'data': QuestionSerializer().to_representation(current_round.question)
            }
        )
    
    def send_round_winner(self):
        print('will send_round_winner', self.user.username)
        current_round = self.get_current_round()
        player_a = current_round.player_a
        player_b = current_round.player_b

        answers = {
            player_a['username']: player_a,
            player_b['username']: player_b
        }

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'round_winner',
                'data': {
                    'winner': current_round.winner.username if current_round.winner else None,
                    'answers': answers
                }
            }
        )

    # Send message to WebSocket
    def send_to_websocket(self, type, data):
        self.send(text_data=json.dumps({
            'type': type,
            'data': data
        }))

    def chat_message(self, event):
        self.send_to_websocket('chat_message', event['data'])
    
    def question_update(self, event):
        self.send_to_websocket('question_update', event['data'])

    def round_winner(self, event):
        self.send_to_websocket('round_winner', event['data'])
    
    def notification(self, event):
        self.send_to_websocket('notification', event['data'])
    
    def game_update(self, event):
        self.send_to_websocket('game_update', event['data'])
    
    def scores_update(self, event):
        self.send_to_websocket('scores_update', event['data'])

    def connected(self, evet):
        print('connected event')


from django.core.cache import cache

class InvitationConsumer(WebsocketConsumer):
    def connect(self):
        cache.set('INVITATIONS_CHANNEL', self.channel_name, timeout=None)
        self.group_name = 'online_users'
        self.user = self.scope['user']

        print(self.user, 'is now online')

        if self.user:
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
        else:
            self.close()

    def receive(self, text_data=None, bytes_data=None):
        pass

    def game_invitation(self, event):
        data = event['data']
        print(data['invited_by']['username'], 'invited', data['invited'], 'to play at', data['channel'])
        self.send(text_data=json.dumps({
            'type': 'game_invitation',
            'data': data
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )



websocket_urlpatterns = [
    re_path(r'^ws/game/(?P<user_token>[^/]+)/(?P<room_name>[^/]+)/$', QueryAuthMiddleware(GameConsumer.as_asgi())),
    re_path(r'^ws/invitations/(?P<user_token>[^/]+)/$', QueryAuthMiddleware(InvitationConsumer.as_asgi())),
]