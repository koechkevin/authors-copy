from django.urls import path
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView, VerifyAPIView, SocialSignUp, EmailSentAPIView, PasswordResetAPIView
)
# Specify a namespace
app_name="authentication"

urlpatterns = [
    path('user/', UserRetrieveUpdateAPIView.as_view()),
    path('users/', RegistrationAPIView.as_view(), name='user-registration'),
    path('users/login/', LoginAPIView.as_view(), name='user_login'),
    path('verify/<str:token>', VerifyAPIView.as_view(), name='verify'),
    path('users/email_sent', EmailSentAPIView.as_view(), name='email_password'),
    path('users/password_reset', PasswordResetAPIView.as_view(), name='password_reset'),
    path('social_auth/', SocialSignUp.as_view(), name="social_sign_up"),
]
