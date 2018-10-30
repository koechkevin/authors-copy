# authors/authentication/token.py
# This file generates token using a username

from datetime import datetime, timedelta
import jwt
from django.conf import settings

def generate_token(username):
        """
        This method generates and return it as a string.
        """
        date = datetime.now() + timedelta(hours=24)

        payload = {
            'username': username,
            'exp': int(date.strftime('%s'))
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        return token.decode()
