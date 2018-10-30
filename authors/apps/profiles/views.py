from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ValidationError
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework import status

from authors.apps.authentication.models import User
from .models import Profile
from .renderers import ProfileJSONRenderer, ProfilesJSONRenderer
from .serializers import ProfileSerializer, ProfileListSerializer
from authors.apps.authentication.serializers import UserSerializer

def current_profile(request):
    authenticated_user=request.user
    return authenticated_user.profile

def followed_profile(username):
    profile_to_follow=Profile.objects.get(user__username=username)
    return profile_to_follow

class ProfileAPIView(APIView):
    #Allow any user to hit this endpoint
    permission_classes = (IsAuthenticatedOrReadOnly,)
    renderer_classes = (ProfileJSONRenderer,)

    def get(self, request, username, format=None):
        try:
            profile =  Profile.objects.get(user__username=username)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response(
                {
                    'message': 'Profile not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, username, format=None):
        try:
            serializer_data = request.data.get('user', {})
            serializer = ProfileSerializer(request.user.profile, data=serializer_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                    {
                        'message': 'Profile not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )


class FollowCreate(CreateAPIView):

    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def post(self, request, username):
        """Follow user"""

        #get current user

        following_user = current_profile(request)

        # check if the user to be followed exists
        try:
            followed_user = followed_profile(username)
        except Profile.DoesNotExist:
            raise NotFound('You are trying to follow a user who in not there, please check the username again')

        # Check if user is trying to follow himself
        if following_user.id == followed_user.id:
            raise ValidationError("You cannot follow yourself")

        # Add user
        following_user.follow(followed_user)

        serialize = self.serializer_class(following_user, context={'request': request})
        return Response(data=serialize.data, status=status.HTTP_201_CREATED)


    def delete(self, request, username):
        """Unfollow user"""

        #get current user

        following_user = current_profile(request)

        # check if the user to unfollowed be exists
        try:
            followed_user = followed_profile(username)
        except Profile.DoesNotExist:
            raise NotFound('You are trying to unfollow a user who in not there,please check the username again')

        # Check if user trying to unfollow him/herself
        if following_user.id == followed_user.id:
            raise ValidationError("You cannot unfollow yourself")

        # unfollow user
        following_user.unfollow(followed_user)

        serialize = self.serializer_class(following_user, context={'request': request})
        return Response(data=serialize.data, status=status.HTTP_200_OK)

class Following(generics.RetrieveAPIView):
    """
    Get all the users a user follows
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request, username):
        """Following"""

        following_user = current_profile(request)
        followed_user = followed_profile(username)

        following = following_user.following(followed_user)

        serializer = self.serializer_class(following, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FollowedBy(generics.RetrieveAPIView):
    """
    Get all the users who follow a user
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request, username):
        """Followers"""

        following_user = current_profile(request)
        followed_user = followed_profile(username)

        follower = following_user.followers(followed_user)

        serializer = self.serializer_class(follower, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ProfilesJSONRenderer,)

    def get(self, request):
        """
        List of profiles for other users
        """
        try:
            queryset = Profile.objects.all().exclude(user=request.user)
        except Profile.DoesNotExist:
            message = Response(
                    {
                        'message': 'Profile not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        serializer = ProfileListSerializer(queryset, many=True)
        message = Response({'profiles': serializer.data}, status=status.HTTP_200_OK)
        return message
