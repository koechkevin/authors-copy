from rest_framework import status, generics
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import User
from social_django.utils import load_backend, load_strategy
from social.backends.oauth import BaseOAuth1, BaseOAuth2
from social_core.exceptions import AuthAlreadyAssociated, MissingBackend
from .renderers import UserJSONRenderer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer, EmailSerializer, PasswordResetSerializer, SocialSignUpSerializer
)
from .password_token import generate_password_token, get_password_token_data
import os
from django.template.loader import render_to_string

from .token import generate_token
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
import jwt
from .models import User


class RegistrationAPIView(CreateAPIView):
    # Allow any user (authenticated or not) to hit this endpoint.
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        user = request.data.get('user', {} )

        # The create serializer, validate serializer, save serializer pattern
        # below is common and you will see it a lot throughout this course and
        # your own work later on. Get familiar with it.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        user_email = user['email']
        user_name = user['username']
        token = generate_token(user_name)
        current_domain = settings.DEFAULT_DOMAIN

        # send email to the user for verification
        url = current_domain + "/api/verify/" + str(token)
        body = render_to_string('verify.html', {
            'link': url,
            'name': user_name
        })
        send_mail(
            'Verify your email',
            'Please verify your account.',
            'no-reply@authors-heaven.com',
            [user_email],
            html_message = body,
            fail_silently=False,
        )
        content = "Thank you for registering at Authors heaven."\
        "To start using authors heaven, go to your email and click the confirmation "\
        "link which we haves sent to you :D"
        return_message = {"Message": content}
        serializer.save()
        return Response(return_message, status=status.HTTP_201_CREATED)

class LoginAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        # There is nothing to validate or save here. Instead, we just want the
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer_data = request.data.get('user', {})

        # Here is that serialize, validate, save pattern we talked about
        # before.
        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

class VerifyAPIView(APIView):
    """
    A class to verify user using the token sent to the email
    """
    permission_classes = (AllowAny,)
    def get(self, request, token):
        try:
            username = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_in_db = User.objects.get(username=username['username'])
            user_in_db.is_active = True
            user_in_db.save()
            return Response(data={"Message": "Congratulations! You have successfully activated your account."},
                            status=status.HTTP_200_OK)
        except:
            return Response(data={"Message": "Invalid link"},
                            status=status.HTTP_400_BAD_REQUEST)
class EmailSentAPIView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = EmailSerializer

    def post(self, request):
        """
        here, the user provides email to be used to get a link. The email must be registered,
        token gets generated and sent to users via link.
        """
        email = request.data.get('email', {})
        serializer = self.serializer_class(data={'email':email})
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            message = {"message":"The email provided is not registered"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        token_generator = PasswordResetTokenGenerator()
        password_token = token_generator.make_token(user)
        token = generate_password_token(email, password_token)
        message = {"message":"We've sent a password reset link to your email"}
        subject = "Password reset"
        reset_link = os.getenv('PASSWORD_RESET')
        body = render_to_string('password_reset.html', {
            'link':reset_link+'?token=' + token,
            'name': user.username,
        })
        sender = os.getenv('EMAIL_SENDER')
        send_mail(subject, "Password Reset", sender, [email], html_message=body)
        return Response(message, status=status.HTTP_200_OK)

class PasswordResetAPIView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = PasswordResetSerializer

    def put(self, request):
        """
        Here, the user has received an email with a link to reset password.
        The user provides a new password.
        Token gets verified against the user.
        Once all checks have passed, the new password gets saved.
        """
        user_token = request.GET.get("token", "")
        try:
            token_data = get_password_token_data(user_token)
            if not token_data['email']:
                return Response({"message":"invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except :
            return Response({"message":"invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        password = request.data.get('password', {})
        email = token_data['email']
        data = {
            "email": email,
            "password": password
            }
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            message = {"message":"The Email provided is not registered"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        token = token_data['token']
        token_generator = PasswordResetTokenGenerator()
        checked_token = token_generator.check_token(user, token)
        if not checked_token:
           return Response({"message":"invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(user, data=data)
        serializer.is_valid(raise_exception=True)
        user.set_password(password)
        user.save()
        return Response({"message": "password successfully changed"}, status=status.HTTP_200_OK)


class SocialSignUp(CreateAPIView):
    renderer_classes = (UserJSONRenderer,)
    serializer_class = SocialSignUpSerializer
    #allow everyone to view without having to be authenticated
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        """
        Override `create` instead of `perform_create` to access request
        request is necessary for `load_strategy`
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.data['provider']

        # If this request was made with an authenticated user, try to associate this social 
        # account with it
        authed_user = request.user if not request.user.is_anonymous else None
        strategy = load_strategy(request)
        #Get the backend that is associated with the user provider i.e google,twitter and facebook
        backend = load_backend(strategy=strategy, name=provider, redirect_uri=None)


        if isinstance(backend, BaseOAuth1):
           #cater for services that use OAuth1, an example is twitter
            token = {
                'oauth_token': serializer.data['access_token'],
                'oauth_token_secret': request.data['access_token_secret'],
            }
            
        elif isinstance(backend, BaseOAuth2):
            #we just need to pass access_token for OAuth2
            token = serializer.data['access_token']
            

        try:
            #check if the user exists, if exists,we just login but if not it creates a new user
            user = backend.do_auth(token, user=authed_user)
        except AuthAlreadyAssociated:
            # if the user already exists,throw the following error
            return Response({"error": "The email is already registered, please try another one"},
                            status=status.HTTP_400_BAD_REQUEST)

        if user and user.is_active:
            serializer = UserSerializer(user)
            # if the access token was set to an empty string, then save the access token 
            # from the request
            auth_created = user.social_auth.get(provider=provider)
            if not auth_created.extra_data['access_token']:
                # Facebook for example will return the access_token in its response to you. 
                auth_created.extra_data['access_token'] = token
                auth_created.save()
                serializer.save()

            
            serializer.instance = user
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, 
                            headers=headers)
        else:
            return Response({"error": "Something went wrong with the authentication, please try again"},
                                        status=status.HTTP_400_BAD_REQUEST)
