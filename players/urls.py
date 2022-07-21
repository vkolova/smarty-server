from django.urls import path, include
from rest_framework import routers
from .views import PlayerView, PlayersList, MyProfile

router = routers.SimpleRouter()
router.register(r'player', PlayerView)
router.register(r'players', PlayersList)
router.register(r'players/me', MyProfile)

urlpatterns = [
    path('', include(router.urls))
]