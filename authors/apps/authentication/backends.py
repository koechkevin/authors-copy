import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User



"""Configure JWT Here"""
class JWTAuthentication(authentication.BaseAuthentication):
    """
    This is called on every request to check if the user is authenticated
    """

    def authenticate(self, request):
        """
        This checks that the passed JWT token is valid and returns
        a user and his/her token on successful verification
        """

        # Get the passed token
        token = authentication.get_authorization_header(request)

        # Ensure we have a token
        if not token:
            return None

        # Attempt decoding the token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY)
        except:
            raise AuthenticationFailed('Invalid token.')

        # Get the user owning the token
        try:
            user = User.objects.get(email=payload['email'])
        except User.DoesNotExist:
            raise AuthenticationFailed('No user found for token provided')

        # Check this user is activated
        if not user.is_active:
            raise AuthenticationFailed('This user is deactivated')

        return (user, token)
