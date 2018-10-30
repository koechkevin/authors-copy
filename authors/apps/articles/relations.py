import re
from rest_framework import serializers
from django.utils.text import slugify

from authors.apps.articles.models import Tags


class TagsRelation(serializers.RelatedField):
    """This class overwrites the serializer class for tags
    to enable tags to be saved on a separate table when
    creating an article
    """

    def get_queryset(self):
        return Tags.objects.all()

    def to_representation(self, value):
        return value.tag

    def to_internal_value(self, data):
        # Ensures tags with CAPS and spaces are saved as slugs
        # Capitalize characters and small letter characters are saved as one
        if not re.match(r'^[a-zA-Z0-9][ A-Za-z0-9_-]*$', data):
            raise serializers.ValidationError('Tag cannot have special characters')
        new_tag = slugify(data)
        tag, created = Tags.objects.get_or_create(tag=new_tag)
        return tag

