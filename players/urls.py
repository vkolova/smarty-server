from django.urls import path, include
from rest_framework import routers
from .views import PlayerView, PlayersList

router = routers.SimpleRouter()
router.register(r'player', PlayerView)
router.register(r'players', PlayersList)

urlpatterns = [
    path('', include(router.urls))
]