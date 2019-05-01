from django.conf.urls import url
from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import asyncio
from asgiref.sync import async_to_sync
import json
import random
from datetime import datetime

from django.contrib.auth.models import User
from players.models import Player
from questions.models import Question
from questions.serializers import QuestionSerializer
from games.models import Game, Round, GameState
from games.serializers import GameSerializer

GAME_ROUNDS_COUNT = 10
QUESTION_POINTS = 10

class GameController(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_uuid = self.scope['url_route']['kwargs']['game_uuid']
        self.game_group = 'game_%s' % self.game_uuid
        
        self.user = await self.get_user()
        print(self.user.username, 'connected to socket')

        await self.channel_layer.group_add(
            self.game_group,
            self.channel_name
        )

        await self.accept()
        await self.send_game_update()
    
    @property
    @database_sync_to_async
    def game(self):
        return Game.objects.get(channel=self.game_uuid)

    @database_sync_to_async
    def save(self, item):
        item.save()
    
    def initialize_game_data(self):
        data = {
            'connected': [],
            'round': self.initialize_round_data(),
            'score': self.players_obj(0) 
        }
        return data

    async def save_connected(self):
        game = await self.game
        if not game.data:
            game.data = {
                'connected': [],
                'round': self.initialize_round_data(),
                'score': self.players_obj(0) 
            }
        else:
            print("!!!!")
            connected = game.data['connected']
            connected.append(self.user.username)
            game.data['connected'] = list(set(connected)) # remove dublicates
            # await database_sync_to_async(game.save)()
        # import pdb; pdb.set_trace()
        # await game.save()
        # await database_sync_to_async(game.save)()
        await self.save(game)

        print('notify connected')
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': 'Connected.'
        }))
        

    def initialize_round_data(self):
        player_data = {
            'timestamp': None,
            'is_correct': None
        }
        return self.players_obj(player_data)

    async def check_all_connected(self):
        game = await self.game
        print("game.data", game.data, game)
        print("        ", game.data['connected'])

        if len(game.data['connected']) == 0:
            return False

        for u in game.players.values():
            print("---", u['username'], game.data['connected'], u['username'] in game.data['connected'])
            if u['username'] not in game.data['connected']:
                return False
        
        return True

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data = text_data_json['data']
        type = text_data_json['type']
        print("~~", "receive", self.user.username, data)

        if type == 'game_connect':
            await self.game_connect(text_data_json)
        if type == 'question_answer':
            await self.question_answer(text_data_json)
    
    async def players_obj(self, value):
        game = await self.game
        data = {}
        for p in [u['username'] for u in game.players.values()]:
            data[p] = value
        return data

    async def start_game(self):
        game = await self.game
        if game.state != 'in_progress':
            await self.new_round()
            await database_sync_to_async(game.save)()
        else:
            await self.send_question_update()

        await self.send_score_update()
        game.state = GameState.IN_PROGRESS
        await database_sync_to_async(game.save)()
        await self.send_game_update()
    
    async def game_connect(self, event):
        print('game_connect')
        game = await self.game
        data = event['data']
        print("data: ", data)
        if data == 'ok':
            print('connect', self.user)
            await self.save_connected()
            players_are_connected = await self.check_all_connected()

            if players_are_connected:
                print('all are connected')
                await self.start_game()
        else:
            game.state = GameState.DECLINED
            game.finished = datetime.now()
            await database_sync_to_async(game.save)()
            await self.send_game_update()
    
    async def get_current_round(self):
        return await self.game.rounds.order_by('-id')[0]
    
    async def send_game_update(self):
        await self.channel_layer.group_send(
            self.game_group,
            {
                'type': 'game_update',
                'data': GameSerializer().to_representation(await self.game)
            }
        )
    
    async def game_update(self, event):
        pass

    async def send_score_update(self):
        await self.channel_layer.group_send(
            self.game_group,
            {
                'type': 'scores_update',
                'data': await self.game.data['score']
            }
        )
    
    async def send_question_update(self):
        current_round = await self.get_current_round()
        await self.channel_layer.group_send(
            self.game_group,
            {
                'type': 'question_update',
                'data': QuestionSerializer().to_representation(current_round.question)
            }
        )
    
    @database_sync_to_async
    def get_user(self):
        token = self.scope['url_route']['kwargs']['user_token']
        return User.objects.get(auth_token=token)
    
    @database_sync_to_async
    def get_question(self):
        count = Question.objects.all().count()
        slice = random.random() * (count - 1)
        question = Question.objects.all()[slice: slice+1][0]
        return question

    async def new_round(self):
        game = self.game
        game.data['score'] = self.players_obj(0)
        await database_sync_to_async(game.save)()
        question = await self.get_question()
        self.current_round = Round.objects.create(game=self.game, question=question)
        await self.send_question_update()

    # def game_message(self, event):
    #     data = event['data']

    #     self.send(text_data=json.dumps({
    #         'data': data
    #     }))
    
    async def check_all_answered(self):
        game = await self.game
        current_round = self.get_current_round()

        for p in [u['username'] for u in game.players.values()]:
            if not game.data['round'][p]['timestamp']:
                return False
        return True

    @database_sync_to_async
    async def select_round_winner(self):
        game = await self.game
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
            current_round.winner = Player.objects.get(username=winner)
            await database_sync_to_async(current_round.save)()

    async def send_round_winner(self):
        current_round = self.get_current_round()
        data = {
            'type': 'round_winner',
            'data': current_round.winner.username if current_round.winner else None
        }

        await self.channel_layer.group_send(
            self.game_group,
            data
        )

    async def is_score_a_tie(self):
        game = await self.game
        score_data = game.data['score']

        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']

        return score_data[player_a] == score_data[player_b]

    async def check_game_end(self):
        game = await self.game
        rounds_count = len(game.rounds.all())
        is_a_tie = self.is_score_a_tie()

        if rounds_count == GAME_ROUNDS_COUNT and is_a_tie:
            return False
        else:
            return rounds_count == GAME_ROUNDS_COUNT

    @database_sync_to_async
    async def finish_game(self):
        game = await self.game
        score_data = game.data['score']

        player_a = game.players.values()[0]['username']
        player_b = game.players.values()[1]['username']

        p_a = Player.objects.get(username=player_a)
        p_a.score = p_a.score + score_data[player_a]
        await database_sync_to_async(p_a.save)()

        p_b = Player.objects.get(username=player_b)
        p_b.score = p_b.score + score_data[player_b]
        await database_sync_to_async(p_b.save)()

        game.winner = p_a if score_data[player_a] > score_data[player_b] else p_b
        game.state = GameState.FINISHED
        game.finished = datetime.now()
        await database_sync_to_async(game.save)()

    async def initialize_next_round(self):
        await self.new_round()

    async def question_answer(self, event):
        data = event['data']
        print("~~", 'question_answer', self.user.username, data)
        game = await self.game
        user = self.user.username
        current_round = await self.get_current_round()

        is_correct = data == current_round.question.correct_answer()

        game.data['round'][user] = {
            'timestamp': datetime.now().timestamp(),
            'is_correct': is_correct
        }
        await database_sync_to_async(game.save)()

        if await self.check_all_answered():
            print("self.check_all_answered()", True)
            await self.select_round_winner()
            await self.send_round_winner()

            if await self.check_game_end():
                await self.finish_game()
                await self.send_game_update()
            else:
                await self.initialize_next_round()

websocket_urlpatterns = [
    url(r'^ws/game/(?P<user_token>[^/]+)/(?P<game_uuid>[^/]+)/$', GameController),
]