from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from datetime import datetime

from django.conf.urls import url
from django.contrib.auth.models import User
from django.db import connection

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

class GameController(WebsocketConsumer):
    def connect(self):
        self.game_uuid = self.scope['url_route']['kwargs']['game_uuid']
        self.game_group = 'game_%s' % self.game_uuid
        
        self.user = self.get_user()
        print(self.user.username, 'connected to socket')

        async_to_sync(self.channel_layer.group_add)(
            self.game_group,
            self.channel_name
        )

        self.accept()
        self.send_game_update()
    
    @property
    def game(self):
        return Game.objects.get(channel=self.game_uuid)
    
    def initialize_game_data(self):
        data = {
            'connected': [],
            'round': self.initialize_round_data(),
            'score': self.players_obj(0) 
        }
        return data

    def save_connected(self):
        game = self.game

        if not game.data:
            game.data = {
                'connected': [ self.user.username ],
                'round': self.initialize_round_data(),
                'score': self.players_obj(0) 
            }
            # game.save()
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
        

    def initialize_round_data(self):
        player_data = {
            'timestamp': None,
            'is_correct': None
        }
        return self.players_obj(player_data)

    def check_all_connected(self):
        print('check_all_connected')

        game = self.game
        

        print("~~~", game.data)

        if len(game.data['connected']) == 0:
            return False

        for u in game.players.values():
            print("---", u['username'], game.data['connected'], u['username'] in game.data['connected'])
            if u['username'] not in game.data['connected']:
                return False
        
        return True

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.game_group,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data = text_data_json['data']
        type = text_data_json['type']
        print("~~", "receive", self.user.username, data)

        if type == 'game_connect':
            self.game_connect(text_data_json)
        if type == 'question_answer':
            self.question_answer(text_data_json)
    
    def players_obj(self, value):
        game = self.game
        

        data = {}
        for p in [u['username'] for u in game.players.values()]:
            data[p] = value
        return data

    def start_game(self):
        game = self.game
        if game.state != 'in_progress':
            self.new_round()
            # game.save()
        else:
            self.send_question_update()

        self.send_score_update()
        game.state = GameState.IN_PROGRESS
        game.save()
        
        self.send_game_update()
    
    def game_connect(self, event):
        print('game_connect')
        game = self.game
        data = event['data']
        print("data: ", data)

        if data == 'ok':
            print('connect', self.user)
            self.save_connected()
        
            sleep(2)
            players_are_connected = self.check_all_connected()

            if self.check_all_connected():
                print('all are connected')
                self.start_game()
        else:
            game.state = GameState.DECLINED
            game.finished = datetime.now()
            game.save()
        self.send_game_update()
    
    def get_current_round(self):
        current_round = self.game.rounds.order_by('-id')[0]
        
        return current_round
    
    def send_game_update(self):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group,
            {
                'type': 'game_update',
                'data': GameSerializer().to_representation(self.game)
            }
        )
        
        # self.send(text_data=json.dumps({
        #     'type': 'game_update',
        #     'data': GameSerializer().to_representation(self.game)
        # }))
    
    def game_update(self, event):
        print('game_update')
        self.send(text_data=json.dumps({
            'type': 'game_update',
            'data': event['data']
        }))
    
    def scores_update(self, event):
        print('scores_update')
        self.send(text_data=json.dumps({
            'type': 'scores_update',
            'data': event['data']
        }))

    def send_score_update(self):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group,
            {
                'type': 'scores_update',
                'data': self.game.data['score']
            }
        )
        
        # self.send(text_data=json.dumps({
        #     'type': 'scores_update',
        #     'data': self.game.data['score']
        # }))
    
    def send_question_update(self):
        print('send_question_update')
        current_round = self.get_current_round()

        async_to_sync(self.channel_layer.group_send)(
            self.game_group,
            {
                'type': 'question_update',
                'data': QuestionSerializer().to_representation(current_round.question)
            }
        )

        # self.send(text_data=json.dumps({
        #     'type': 'question_update',
        #     'data': QuestionSerializer().to_representation(current_round.question)
        # }))


    def get_user(self):
        token = self.scope['url_route']['kwargs']['user_token']
        user = User.objects.get(auth_token=token)
        
        return user
    
    def get_question(self):
        count = Question.objects.all().count()
        slice = random.random() * (count - 1)
        question = Question.objects.all()[slice: slice+1][0]
        return question

    def new_round(self):
        game = self.game
        game.data['round'] = self.initialize_round_data()
        game.save()
        
        question = self.get_question()
        
        self.current_round = Round.objects.create(game=self.game, question=question)
        
        
        self.send_question_update()
    
    def check_all_answered(self):
        game = self.game
        
        current_round = self.get_current_round()

        for p in [u['username'] for u in game.players.values()]:
            if not game.data['round'][p]['timestamp']:
                return False
        return True

    def select_round_winner(self):
        game = self.game
        current_round = self.get_current_round()
        round_data = game.data['round']

        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']

        # print("select winner:", round_data[player_a]['timestamp'], round_data[player_b]['timestamp'])

        if round_data[player_a]['is_correct'] and round_data[player_b]['is_correct']:
            winner = player_a if round_data[player_a]['timestamp'] < round_data[player_b]['timestamp'] else player_b
        elif round_data[player_a]['is_correct'] and not round_data[player_b]['is_correct']:
            winner = player_a
        elif not round_data[player_a]['is_correct'] and round_data[player_b]['is_correct']:
            winner = player_b
        else:
            winner = None
        
        if winner:
            game.data['score'][winner] = game.data['score'][winner] + QUESTION_POINTS
            game.save()
            current_round.winner = Player.objects.get(username=winner)
            current_round.save()
        

    def send_round_winner(self):
        current_round = self.get_current_round()
        async_to_sync(self.channel_layer.group_send)(
            self.game_group,
            {
                'type': 'round_winner',
                'data': current_round.winner.username if current_round.winner else None
            }
        )
        # self.send(text_data=json.dumps(data))

    def is_score_a_tie(self):
        game = self.game
        
        score_data = game.data['score']

        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']

        return score_data[player_a] == score_data[player_b]

    def check_game_end(self):
        print('check_game_end')
        game = self.game
        

        rounds_count = len(game.rounds.all())
        print("ROUND", rounds_count)
        is_a_tie = self.is_score_a_tie()

        if rounds_count == GAME_ROUNDS_COUNT and is_a_tie:
            return False
        else:
            return rounds_count == GAME_ROUNDS_COUNT

    def finish_game(self):
        game = self.game
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
        

    def initialize_next_round(self):
        self.new_round()
        self.send_score_update()
        self.send_game_update()

    def question_answer(self, event):
        data = event['data']
        print("~~", 'question_answer', self.user.username, data)
        game = self.game
        user = self.user.username
        current_round = self.get_current_round()

        is_correct = data == current_round.question.correct_answer()

        print("------------", game.data['round'])
        game.data['round'][user] = {
            'timestamp': datetime.now().timestamp(),
            'is_correct': is_correct
        }
        game.save()
        

        if self.check_all_answered():
            print("self.check_all_answered()", True)
            self.select_round_winner()
            self.send_round_winner()

            if self.check_game_end():
                self.finish_game()
                self.send_game_update()
            else:
                self.initialize_next_round()
    
    def question_update(self, event):
        print('question_update')
        self.send(text_data=json.dumps({
            'type': 'question_update',
            'data': event['data']
        }))

    def round_winner(self, event):
        print('round_winner')
        self.send(text_data=json.dumps({
            'type': 'round_winner',
            'data': event['data']
        }))
    

websocket_urlpatterns = [
    url(r'^ws/game/(?P<user_token>[^/]+)/(?P<game_uuid>[^/]+)/$', GameController),
]