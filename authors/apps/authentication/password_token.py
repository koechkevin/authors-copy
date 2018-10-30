# generates token used bu user to reset password
import datetime
import jwt
from .models import User
from django.conf import settings

def  generate_password_token(email, password_token):
    """
    generates token appended to url
    """
    time = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    payload = {
        'email':email,
        'token':password_token,
        'exp': time
    }
    token = jwt.encode(payload, settings.SECRET_KEY)
    return token.decode('utf-8')

def get_password_token_data(token):
    """
    checks validity of a token
    """
    try:
        raw_data = jwt.decode(token, settings.SECRET_KEY)
    except jwt.InvalidTokenError:
        return {'':''}
    email = raw_data['email']
    password_token = raw_data['token']
    return {'email':email, 'token':password_token}