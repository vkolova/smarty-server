from django.contrib import admin
from django.conf.urls import include, url

api_patterns = [
    url(r'^accounts/', include('accounts.urls')),
    url(r'^', include('players.urls')),
    url(r'^', include('games.urls')),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(api_patterns)),
]
