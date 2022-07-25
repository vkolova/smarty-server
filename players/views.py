from rest_framework import serializers, mixins, permissions, viewsets, status, generics
from rest_framework.response import Response

from .models import Player
from .serializers import PlayerSerializer


class PlayerView(mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin,
                viewsets.GenericViewSet):
    
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=user, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PlayersList(viewsets.ViewSet):
    queryset = Player.objects.all()
    serializer_class = Player

    def list(self, request):
        queryset = Player.objects.all().order_by('-score')
        serializer = PlayerSerializer(queryset[0:10], many=True)

        return Response({
            'players': serializer.data,
            'you': list(queryset.values_list('pk', flat=True)).index(request.user.pk)
        })

class MyProfile(viewsets.ViewSet):
    queryset = Player.objects.all()
    serializer_class = Player

    def list(self, request):
        me = Player.objects.get(user=request.user)
        serializer = PlayerSerializer(me)

        return Response(serializer.data)