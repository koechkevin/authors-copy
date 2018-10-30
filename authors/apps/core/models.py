from django.db import models


class TimeStampedModel(models.Model):
    """Extension class to add timestamp created_at and modified_at to all models
        that inherit from it    
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True