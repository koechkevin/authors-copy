#  authors/apps/notifications
# Contains the views for the notifications

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from authors.apps.notifications.models import UserNotifications
from authors.apps.authentication.models import User
from rest_framework.permissions import IsAuthenticated

from authors.apps.authentication.serializers import (UserSerializer)
from .serializers import NotificationSerializer


class NotificationAPIView(generics.ListAPIView):
    """
    A View that returns notifications
    """
    renderer_classes = (JSONRenderer, )
    permission_classes = (IsAuthenticated,)
    def get(self, request, format=None):
        notifications = UserNotifications.objects.all()
        serializer = NotificationSerializer(notifications, many=True, read_only=True)
        return Response({"notifications": serializer.data})


class SubscribeAPIView(generics.ListAPIView):
    """
    A view for subscribing for notifications
    """

    renderer_classes = (JSONRenderer, )
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    def get(self, request):
        email = request.user
        user = User.objects.get(email=email)
        if user.is_subcribed == True:
            return Response({"Message": "You are already subscribed to notifications"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.is_subcribed = True
            user.save()
            return Response({"Message": "You have successfully subscribed to notifications"}, status=status.HTTP_200_OK)


class UnSubscribeAPIView(generics.ListAPIView):
    """
    A view for Unsubcribing for notifications
    """

    renderer_classes = (JSONRenderer, )
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    def get(self, request):
        email = request.user
        user = User.objects.get(email=email)
        if user.is_subcribed == False:
            return Response({"Message": "You are not subscribed to notifications"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.is_subcribed = False
            user.save()
            return Response({"Message": "You have successfully unsubscribed to notifications"})