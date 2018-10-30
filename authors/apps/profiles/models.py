from django.db import models
from authors.apps.core.models import TimeStampedModel

from django.db.models.signals import post_save
from django.dispatch import receiver

from authors import settings

# Create your models here.
class Profile(TimeStampedModel):
    """
    This class cretes the user profile model
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=255, default='Update your bio')
    image_url = models.URLField(max_length=250, default="image-url", null=True)
    # The related_name attribute specifies the name of the reverse relation from 
    # the Profile model back to itself.
    # symmetrical=False results in creating one row
    isfollowing= models.ManyToManyField('self', related_name='is_following',symmetrical=False)
    def __str__(self):
        return self.user.username

    def follow(self, profile):
        self.isfollowing.add(profile)

    def unfollow(self, profile):
        self.isfollowing.remove(profile)

    def followers(self, profile):
        return profile.is_following.all()

    def following(self, profile):
        return profile.isfollowing.all()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_save_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        instance.profile.save()
