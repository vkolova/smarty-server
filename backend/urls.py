from django.contrib import admin
from django.urls import include, re_path

api_patterns = [
    re_path(r'^accounts/', include('accounts.urls')),
    re_path(r'^', include('players.urls')),
    re_path(r'^', include('games.urls')),
]

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^api/', include(api_patterns)),
]
