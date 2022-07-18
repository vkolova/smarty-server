from django.urls import include, re_path

from .views import (
    CreateUserAPIView,
    LogoutUserAPIView,
    LoginUserAPIView
)

urlpatterns = [
    re_path(r'^login/$',
        LoginUserAPIView.as_view(),
        name='auth_user_login'),
    re_path(r'^register/$',
        CreateUserAPIView.as_view(),
        name='auth_user_create'),
    re_path(r'^logout/$',
        LogoutUserAPIView.as_view(),
        name='auth_user_logout')
]