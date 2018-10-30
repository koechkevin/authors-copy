# authors/apps/notifications/serializers.py

from rest_framework import serializers
from authors.apps.articles.models import ArticlesModel
from authors.apps.authentication.models import User
from authors.apps.notifications.models import UserNotifications 


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        """
        Notification fields to be returned to users
        """
        model = UserNotifications
        fields = ("notification", "read_status", "created_at", "article", "author", "recipient", "article_link")
