from django.contrib.auth.models import User
from django.shortcuts import render

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import CreateUserSerializer
from players.serializers import PlayerSerializer
from players.models import Player


class CreateUserAPIView(CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        token = Token.objects.create(user=serializer.instance)
        token_data = {"token": token.key}

        player, created = Player.objects.get_or_create(user=serializer.instance, avatar="https://s3.r29static.com/bin/entry/aa6/0,200,2000,2000/x,80/1527036/image.jpg")
        return Response(
            {'user': PlayerSerializer().to_representation(player), **token_data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class LoginUserAPIView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        player = Player.objects.get(user=user)
        return Response({ 'token': token.key, 'user': PlayerSerializer().to_representation(player) })


class LogoutUserAPIView(APIView):
    queryset = User.objects.all()

    def get(self, request, format=None):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)