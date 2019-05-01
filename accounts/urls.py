from django.conf.urls import url

from .views import (
    CreateUserAPIView,
    LogoutUserAPIView,
    LoginUserAPIView
)

urlpatterns = [
    url(r'^login/$',
        LoginUserAPIView.as_view(),
        name='auth_user_login'),
    url(r'^register/$',
        CreateUserAPIView.as_view(),
        name='auth_user_create'),
    url(r'^logout/$',
        LogoutUserAPIView.as_view(),
        name='auth_user_logout')
]