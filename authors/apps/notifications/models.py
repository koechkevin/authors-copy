# authors/apps/notifications.py
# Model for the Notification

from django.db import models
from authors.apps.authentication.models import User
from authors.apps.articles.models import ArticlesModel
from django.utils.timezone import now


class UserNotifications(models.Model):
    """ Notification model """
    author = models.ForeignKey(ArticlesModel, related_name="author_id+", on_delete = models.CASCADE, blank=True)
    recipient =  models.ForeignKey(User, to_field="email", on_delete = models.CASCADE, blank=True)
    article = models.ForeignKey(ArticlesModel, to_field="slug", on_delete = models.CASCADE, blank=True)
    notification = models.TextField()
    article_link = models.URLField(
        ("Article Link"), 
        max_length=128, 
        db_index=True,
        blank=True
    )
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Notice " - " : will order by created most recently
        ordering = ('-created_at',)

    def __str__(self):
        "return the notification"
        return "{}".format(self.notification)