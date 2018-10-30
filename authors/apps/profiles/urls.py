from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import ProfileAPIView, ProfileListAPIView, FollowCreate,Following,FollowedBy

app_name = "profiles"

urlpatterns = [
    path('profiles/',ProfileListAPIView.as_view(), name='view_all'),
    path('profiles/<username>/', ProfileAPIView.as_view(), name='user-profile'),
    path('profile/<username>/follow/', FollowCreate.as_view(), name='follow'),
    path('profile/<username>/following/', Following.as_view(), name='following'),
    path('profile/<username>/followers/', FollowedBy.as_view(), name='followers')
]

urlpatterns = format_suffix_patterns(urlpatterns)