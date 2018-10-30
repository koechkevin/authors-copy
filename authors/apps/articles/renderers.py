from rest_framework.renderers import JSONRenderer
import json
from django.db.models import Avg
from rest_framework import renderers, status
from rest_framework.renderers import JSONRenderer

from .models import ArticlesModel, Rating


class ArticlesRenderer(renderers.BaseRenderer):
    """This class determines how the articles should be displayed"""
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """This method overwrites the current render method"""
        # checks if the data received is a list
        if isinstance(data, list):
            # converts it into a dictionary with a key
            return json.dumps(
                {
                    'status': 'success',
                    'articles': data,
                    'article_count': len(data)
                }
            )
        else:
            # checks if the data received is an error message
            error = data.get('detail') or data.get('errors')
            if error:
                return json.dumps(
                    data
                )
            else:
                # if not an error then it must be a single article dictionary
                return json.dumps(
                    {
                        'status': 'success',
                        'article': data
                    }
                )

class FavouriteJSONRenderer(JSONRenderer):
       def render(self, data, media_type=None, renderer_context=None):
        # view exceptions errors...
        if renderer_context:
            code = renderer_context.get('response').status_code
            if not code == status.HTTP_200_OK:
                return_data = {"errors":data}
                return super(FavouriteJSONRenderer, self).render(return_data )
        return super(FavouriteJSONRenderer, self).render(data) 

class RatingJSONRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        # view exceptions errors...
        if renderer_context:
            code = renderer_context.get('response').status_code
            if not code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                return super(RatingJSONRenderer, self).render(data)

        if not renderer_context['request'].user.is_authenticated:
            del data['rating']
        return json.dumps({
            'rating': data
        })
            
