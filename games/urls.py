from rest_framework import routers
from .views import GameView

router = routers.SimpleRouter()
router.register(r'games', GameView)

urlpatterns = router.urls