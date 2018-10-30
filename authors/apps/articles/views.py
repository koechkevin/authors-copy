import os

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView,
                                     GenericAPIView,
                                     ListAPIView, CreateAPIView)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .models import ArticlesModel, Comment, Rating, Favourite, Tags, LikesDislikes, CommentHistory, CommentLike, ArticleStat, ReportArticles, Highlighted
from .serializers import (ArticlesSerializers,
                          CommentsSerializers,
                          RatingSerializer,
                          FavouriteSerializer,
                          TagSerializers,
                          LikesDislikesSerializer,
                          CommentsLikeSerializer,
                          CommentHistorySerializer,
                          ReportArticlesSerializer,
                          ArticleStatSerializer,
                          HighlightedSerializer)
from authors import settings
from .renderers import ArticlesRenderer, RatingJSONRenderer, FavouriteJSONRenderer
from django.template.loader import render_to_string
from django.core.mail import send_mail

from .permissions import IsOwnerOrReadonly
from .models import ArticlesModel
from .serializers import ArticlesSerializers
from .renderers import ArticlesRenderer
from authors.apps.notifications.models import UserNotifications
from .filters import ArticlesFilter
from authors.apps.profiles.models import Profile
from authors.apps.authentication.models import User


class StandardPagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = settings.MAX_PAGE_SIZE

def get_article(slug):
    """
    This method returns article for further reference made to article slug
    """
    article = ArticlesModel.objects.filter(slug=slug).first()
    if not article:
        message = {'message': 'Article slug is not valid.'}
        return message
    # queryset always has 1 thing as long as it is unique
    return article


class ArticlesList(ListCreateAPIView):
    queryset = ArticlesModel.objects.all()
    serializer_class = ArticlesSerializers
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination
    renderer_classes = (ArticlesRenderer,)
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filter_class = ArticlesFilter
    search_fields = ('title', 'description', 'tags__tag', 'author__username')
    ordering_fields = ('title', 'author__username')

    def post(self, request):
        article = request.data.get('article', {})
        serializer = self.serializer_class(
            data=article,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@receiver(post_save, sender=ArticlesModel)
# This receiver handles notification creation immediately a new article is created.
def notification(sender, instance=None, created=None, **kwargs):
    """
    Sends notification
    """
    if created == True:
        username = instance.author.username
        author = instance.author
        title = instance.title
        # domain for the application
        current_domain = settings.DEFAULT_DOMAIN

        # create a link for to the article
        url = (current_domain + "/api/articles/" + str(instance.slug))
        # get the followers
        profile = author.profile
        followers = profile.is_following.all()

        # send notification
        for follower in followers:
            subscription = User.objects.get(username=follower).is_subcribed
            if subscription == True:
                follower_email = User.objects.get(username=follower)
                email = str(follower_email)
                notification = (username + " created a new article about " + title)
                UserNotifications.objects.create(article=instance,
                    notification = notification, author_id=instance.author.id, recipient_id=email, article_link=url)
                name = User.objects.get(username=follower).username
                # send email notification
                body = render_to_string('notification.html', {
                    'url': url,
                    'notification': notification,
                    'name': name
                })
                send_mail(
                    'You have a new notification',
                    'You have a new notification from authors haven',
                    'authors-haven@authors-heaven.com',
                    [email],
                    html_message=body,
                    fail_silently=False,
                )

class ArticlesDetails(RetrieveUpdateDestroyAPIView):
    queryset = ArticlesModel.objects.all()
    serializer_class = ArticlesSerializers
    renderer_classes = (ArticlesRenderer,)
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)
    lookup_field = 'slug'


    def get(self, request, slug):
        article = get_article(slug)
        if isinstance(article, dict):
            raise ValidationError(detail={'artcle': 'No article found for the slug given'})
        if request.user and not isinstance(request.user, AnonymousUser):
            ArticleStat.objects.create(user=request.user, article=article)

        return super().get(request, slug)

    def put(self, request, slug):
        """This method overwrites the """
        article = ArticlesModel.objects.get(slug=slug)
        data = request.data.get('article', {})
        serializer = self.serializer_class(
            article,
            data=data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            self.check_object_permissions(request, article)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        """This method overwrites the default django for an error message"""
        super().delete(self, request, slug)
        return Response({"message": "Article Deleted Successfully"})

    def get_serializer_context(self,*args,**kwargs):
        return {"request":self.request}


class TagsView(ListAPIView):
    queryset = Tags.objects.all()
    serializer_class = TagSerializers
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def list(self, request):
        data = self.get_queryset()
        serializer = self.serializer_class(data, many=True)
        return Response({'tags': serializer.data}, status=status.HTTP_200_OK)


class ArticleStatsView(ListAPIView):
    serializer_class = ArticleStatSerializer

    def get_queryset(self):
       """
       This method filters articles by authors
       """
       return ArticlesModel.objects.filter(author=self.request.user)


class RatingDetails(GenericAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)
    renderer_classes = (RatingJSONRenderer,)

    def get_rating(self, user, article):
        """
        Returns a rating given the user id and the article id
        """
        try:
            return Rating.objects.get(user=user, article=article)
        except Rating.DoesNotExist:
            raise NotFound(detail={'rating': 'Rating not found'})

    def get(self, request, slug):
        """
        Returns the authenticated user's rating on an article given
        its slug.
        """
        article = get_article(slug)
        if isinstance(article, dict):
            raise ValidationError(
                detail={'artcle': 'No article found for the slug given'})

        # If the user is authenticated, return their rating as well, if not or
        # the user has not rated the article return the rating average...
        rating = None
        if request.user.is_authenticated:
            try:
                rating = Rating.objects.get(user=request.user, article=article)
            except Rating.DoesNotExist:
                pass
        if not rating:
            rating = Rating.objects.first()

        serializer = self.serializer_class(rating)
        return Response(serializer.data)

    def post(self, request, slug):
        """
        This will create a rating by user on an article. We also check
        if the user has rated this article before and if that is the case,
        we just update the existing rating.
        """
        article = get_article(slug)
        if isinstance(article, dict):
            raise ValidationError(
                detail={'artcle': 'No article found for the slug given'})
        rating = request.data.get('rating', {})
        rating.update({
            'user': request.user.pk,
            'article': article.pk
        })
        # ensure a user cannot rate their own articles
        if article.author == request.user:
            raise ValidationError(
                detail={'author': 'You cannot rate your own article'})
        # users current rating exists?
        try:
            # if the rating exists, we update it
            current_rating = Rating.objects.get(
                user=request.user.id,
                article=article.id
            )
            serializer = self.serializer_class(current_rating, data=rating)
        except Rating.DoesNotExist:
            # if it doesn't, create a new one
            serializer = self.serializer_class(data=rating)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, article=article)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, slug):
        """
        Gets an existing rating and updates it
        """
        rating = request.data.get('rating', {})
        article = get_article(slug)
        if isinstance(article, dict):
            raise ValidationError(
                detail={'artcle': 'No article found for the slug given'})
        current_rating = self.get_rating(
            user=request.user.id, article=article.id)
        serializer = self.serializer_class(
            current_rating, data=rating, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, article=article)

        return Response(serializer.data)

    def delete(self, request, slug):
        """
        Deletes a rating
        """
        article = get_article(slug)
        if isinstance(article, dict):
            raise ValidationError(
                detail={'artcle': 'No article found for the slug given'})

        rating = self.get_rating(user=request.user, article=article)
        rating.delete()
        return Response(
            {'message': 'Successfully deleted rating'},
            status=status.HTTP_200_OK
        )


class CommentsListCreateView(ListCreateAPIView):
    """
    Class for creating and listing all comments
    """
    queryset = Comment.objects.all()
    serializer_class = CommentsSerializers
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def post(self, request, slug):
        """
        Method for creating article
        """
        article = get_article(slug=slug)
        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        comment = request.data.get('comment', {})
        comment['author'] = request.user.id
        comment['article'] = article.pk
        serializer = self.serializer_class(data=comment)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @receiver(post_save, sender=Comment)
    # This receiver handles notification creation immediately a new article is created.
    def comment_notification(sender, instance=None, created=None, **kwargs):
        """
        Sends notification
        """
        if created == True:
            username = instance.author.username
            author = instance.author
            # domain for the application
            current_domain = settings.DEFAULT_DOMAIN

            # create a link to the article
            url = (current_domain + "/api/articles/" + str(instance.article.slug))
            # get the followers
            recipients = User.objects.all().filter(is_subcribed=True)
            # send notification
            for recipient in recipients:
                id_user = recipient.id
                # check whether user has favorited article being commented
                favourites = Favourite.objects.all().filter(user_id=id_user)
                if len(favourites) == 0:
                    return None
                # if we have some favourites in our records
                elif len(favourites) > 0:
                    for favourite in favourites:
                        # check whether there is a favourite for this article
                        if favourite.article_id == instance.article.id:
                            # fetch the user to notify
                            recipient_email = User.objects.get(id=favourite.user_id)
                            email = str(recipient_email)
                            author_id = instance.author.id

                            notification = (username + " commented on this article about " + instance.article.title)
                            UserNotifications.objects.create(article=instance.article,
                                                             notification=notification, author_id=author_id,
                                                             recipient_id=email, article_link=url)

                            name = User.objects.get(email=email).username
                            # send email notification
                            body = render_to_string('notification.html', {
                                'url': url,
                                'notification': notification,
                                'name': name
                            })
                            send_mail(
                                'You have a new notification',
                                'You have a new notification from authors haven',
                                'authors-haven@authors-heaven.com',
                                [email],
                                html_message=body,
                                fail_silently=False,
                            )

    def get(self, request, slug):
        """
        Method for getting all comments
        """
        article = get_article(slug=slug)
        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)
        comments = article.comments.filter(parent=None)
        serializer = self.serializer_class(comments.all(), many=True)
        data = {
            'count': comments.count(),
            'comments': serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)


class CommentsRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView, ListCreateAPIView):
    """
    Class for retrieving, updating and deleting a comment
    """
    queryset = Comment.objects.all()
    lookup_url_kwarg = 'id'
    serializer_class = CommentsSerializers
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)

    def create(self, request, slug, id):
        """Create a child comment on a parent comment."""
        context = super(CommentsRetrieveUpdateDestroy,
                        self).get_serializer_context()

        article = get_article(slug)
        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)
        parent = article.comments.filter(id=id).first().pk
        if not parent:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        body = request.data.get('comment', {}).get('body', {})

        data = {
            'body': body,
            'parent': parent,
            'article': article.pk,
            'author': request.user.id
        }

        serializer = self.serializer_class(
            data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, slug, id):
        """
        Method for deleting a comment
        """
        article = get_article(slug)
        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        comment = article.comments.filter(id=id)
        if not comment:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        comment[0].delete()
        message = {'detail': 'You have deleted the comment'}
        return Response(message, status=status.HTTP_200_OK)

    def update(self, request, slug, id):
        """
        Method for editing a comment
        """
        article = get_article(slug)
        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        comment = article.comments.filter(id=id).first()
        if not comment:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        new_body = request.data.get('comment',{}).get('body', None)

        # Check if no edit was made, if it was, we want to
        # save the previous comment as history...
        if comment.body != new_body:
            history_data = {
                'body': comment.body,
                'parent': comment.id
            }
            history_serializer = CommentHistorySerializer(data=history_data)
            history_serializer.is_valid(raise_exception=True)
            history_serializer.save()


        new_comment = request.data.get('comment', {}).get('body', None)
        data = {
            'body': new_body,
            'article': article.pk,
            'author': request.user.id
        }
        serializer = self.serializer_class(comment, data=data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class HighlightedDetails(APIView):
    """
    Class for highlighting article content and creating a comment for it
    """
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly, )
    serializer_class = HighlightedSerializer

    def validate_highlight(self, highlight, article):
        index = highlight["index"]
        Body = article.body[index: index + len(highlight["snippet"])]
        return Body == highlight["snippet"]

    def post(self, request, slug):
        # Check if the article exists in the database
        article = get_article(slug)

        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)
        highlight = request.data.get("highlight", {})
        highlight.update({
            'author': request.user.id,
            'article': article.id
        })

        serializer = self.serializer_class(data=highlight)
        serializer.is_valid(raise_exception=True)

        exists = self.validate_highlight(highlight, article)

        if exists:
            serializer.save(author=request.user, article=article)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED
                            )
        return Response({
            "message": "The highlighted snippet does not exist."
        },
            status=status.HTTP_404_NOT_FOUND
        )

    def get(self, request, slug):
        article = get_article(slug)

        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        highlights = Highlighted.objects.filter(article=article.id)

        if highlights:
            serializer = self.serializer_class(highlights.all(), many=True)
            data = {
                'count': highlights.count(),
                'highlights': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response({
            "message": "This article has no highlight snippets"
        },
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request, slug, id):
        highlight = Highlighted.objects.get(pk=id)
        data = request.data.get("highlight", {})
        comment = data["comment"]
        highlight.comment = comment
        highlight.save()
        serializer = self.serializer_class(highlight)
        return Response(serializer.data, status.HTTP_200_OK)


class FavouriteGenericAPIView(APIView):
    serializer_class = FavouriteSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Favourite.objects.all()
    renderer_classes = (FavouriteJSONRenderer,)

    def post(self, request, slug):
        '''method to favourte by adding to db'''
        article = None
        try:
            article = ArticlesModel.objects.get(slug=slug)
        except ArticlesModel.DoesNotExist:
            raise NotFound(detail={"article": [
                "does not exist"
            ]})
        favourite = {}
        favourite["user"] = request.user.id
        favourite["article"] = article.pk
        serializer = self.serializer_class(data=favourite)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        article_serializer = ArticlesSerializers(
            instance=article, context={'request': request})
        data = {"article": article_serializer.data}
        data["article"]["favourited"] = True
        data["message"] = "favourited"
        return Response(data, status.HTTP_200_OK)

    def delete(self, request, slug):
        '''Method to unfavourite by deleting from the db '''
        article = None
        '''get article'''
        try:
            article = ArticlesModel.objects.get(slug=slug)
        except ArticlesModel.DoesNotExist:
            raise NotFound(detail={"article": [
                "does not exist"
            ]})
        "check if they have already unfavourited"
        try:
            favourite = Favourite.objects.get(
                user=request.user.id, article=article.pk)
        except Favourite.DoesNotExist:
            raise NotFound(detail={"message": [
                "you had not favourited this article"
            ]})
        favourite.delete()
        article_serializer = ArticlesSerializers(
            instance=article, context={'request': request})
        data = {"article": article_serializer.data}
        data["message"] = "unfavourited"
        return Response(data, status.HTTP_200_OK)


class ArticlesLikesDislikes(GenericAPIView):
    """
    Class for creating and deleting article likes/dislikes
    """

    queryset = LikesDislikes.objects.all()
    serializer_class = LikesDislikesSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)

    def post(self, request, slug):
        # Check if the article exists in the database
        article = get_article(slug)

        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        like = request.data.get('likes', None)

        # Check if the data in the request a valid boolean
        if type(like) == bool:

            # Check if the article belongs to the current user
            if article.author == request.user:
                message = {'detail': 'You cannot like/unlike your own article'}
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            like_data = {
                'reader': request.user.id,
                'article': article.id,
                'likes': like
            }

            try:
                # Verify if the instance of the article and the user
                # exist in the database and get the like
                user_likes = LikesDislikes.objects.get(
                    article=article.id, reader=request.user.id)

                # if an instance of the user and article both exist in the database
                # we update the existing data instead of creating a new one
                if user_likes:
                    # check if the stored data and the request data are the same
                    # and both true
                    if user_likes.likes and like:
                        return Response(
                            {
                                'detail': '{}, you have already liked this article.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # check if the stored data and the request data are the same
                    # and both false
                    elif not user_likes.likes and not like:
                        return Response(
                            {
                                'detail': '{}, you have already disliked this article.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # check if the stored data and the request data are different
                    # one true and the other false
                    elif like and not user_likes.likes:
                        user_likes.likes = True
                        user_likes.save()
                        article.likes.add(request.user)
                        article.dislikes.remove(request.user)
                        article.save()
                        return Response(
                            {
                                'detail': '{}, you have liked this article.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_200_OK

                        )

                    else:
                        user_likes.likes = False
                        user_likes.save()
                        article.likes.remove(request.user)
                        article.dislikes.add(request.user)
                        article.save()
                        return Response(
                            {
                                'detail': '{}, you have disliked this article.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_200_OK
                        )

            except LikesDislikes.DoesNotExist:
                # Create and save a new like object since one does not exist
                serializer = self.serializer_class(data=like_data)
                serializer.is_valid(raise_exception=True)
                serializer.save(article=article, reader=request.user)

                # if the request data is true, we update the article
                # with the new data
                if like:
                    article.likes.add(request.user)
                    article.save()
                    return Response(
                        {
                            'detail': '{}, you have liked this article.'
                                .format(request.user.username)
                        },
                        status=status.HTTP_201_CREATED
                    )

                # if the request data is false, we update the article
                # with the new data
                else:
                    article.dislikes.add(request.user)
                    article.save()
                    return Response(
                        {
                            'detail': '{}, you have disliked this article.'
                                .format(request.user.username)
                        }
                        , status=status.HTTP_201_CREATED
                    )
        else:

            return Response(
                {
                    'detail': 'Please indicate whether you like/dislike this article.'
                }, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, slug):
        # Check if the article exists in the database
        article = get_article(slug)

        if isinstance(article, dict):
            return Response(article, status=status.HTTP_404_NOT_FOUND)

        try:
            # Verify if the instance of the article and the user
            # exist in the database and get the like
            user_like = LikesDislikes.objects.get(
                article=article.id, reader=request.user.id)
            if user_like:
                if user_like.likes:
                    # If like field in the database is true we remove the count
                    # from the likes field of the article and save the current state
                    article.likes.remove(request.user)
                    article.save()
                else:
                    # If like field in the database is false we remove the count
                    # from the dislikes field of the article and save the current state
                    article.dislikes.remove(request.user)
                    article.save()
        except LikesDislikes.DoesNotExist:
            return Response(
                {
                    'detail': 'Likes/dislikes not found.'
                }, status=status.HTTP_404_NOT_FOUND
            )
        user_like.delete()
        return Response(
            {
                'detail': '{}, your reaction has been deleted successfully.'
                    .format(request.user.username)
            }
            , status=status.HTTP_200_OK
        )


class CommentLikes(GenericAPIView):
    """
    Class for liking an unliking comments
    """

    queryset = CommentLike.objects.all()
    serializer_class = CommentsLikeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)

    def post(self, request, slug, id):
        #Check if a comment exists in the database

        comment = Comment.objects.filter(id=id).first()

        like = request.data.get('comment_likes', None)

        #Check if the data in the request a valid boolean
        if type(like) == bool:

            #Check if the comment belongs to the current user
            if comment.author == request.user:
                message = {'detail': 'You cannot like/unlike your own comment'}
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            like_data = {
                'commentor': request.user.id,
                'specific_comment': comment.id,
                'comment_likes': like
            }

            try:
                #Verify if the instance of the comment and the user
                #exist in the database and get the like
                user_likes = CommentLike.objects.get(specific_comment=comment.id, commentor=request.user.id)

                #if an instance of the user and comment both exist in the database
                #we update the existing data instead of creating a new one
                if user_likes:
                    #check if the stored data and the request data are the same
                    #and both true
                    if user_likes.comment_likes and like:
                        return Response(
                            {
                                'detail':'{}, you have already liked this comment.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    #check if the stored data and the request data are different
                    #one true and the other false
                    elif like and not user_likes.comment_likes:
                        user_likes.comment_likes = True
                        user_likes.save()
                        comment.comment_likes.add(request.user)
                        comment.save()
                        return Response(
                            {
                                'detail': '{}, you have liked this comment.'
                                .format(request.user.username)
                            },
                            status=status.HTTP_200_OK
                        )

            except CommentLike.DoesNotExist:
                #Create and save a new like object since one does not exist
                serializer=self.serializer_class(data=like_data)
                serializer.is_valid(raise_exception=True)
                serializer.save(specific_comment=comment, commentor=request.user)

                #if the request data is true, we update the article
                #with the new data
                if like:
                    comment.comment_likes.add(request.user)
                    comment.save()
                    return Response(
                        {
                            'detail': '{}, you have liked this comment.'
                            .format(request.user.username)
                        },
                        status=status.HTTP_201_CREATED
                    )

                #if the request data is false, we update the article
                #with the new data
        else:

            return Response(
                {
                    'detail': 'Please indicate whether you likethis article.'
                }
                , status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, slug, id):
        #Check if the comment exists in the database

        comment = Comment.objects.filter(id=id).first()
        if isinstance(comment, dict):
            return Response(comment, status=status.HTTP_404_NOT_FOUND)

        try:
            #Verify if the instance of the comment and the user
            #exist in the database and get the like
            user_like = CommentLike.objects.get(specific_comment=comment.id, commentor=request.user.id)
            if user_like:
                if user_like.comment_likes:
                    #If like field in the database is true we remove the count
                    #from the likes field of the article and save the current state
                    comment.comment_likes.remove(request.user)
                    comment.save()

        except CommentLike.DoesNotExist:
            return Response(
                {
                    'detail': 'Likes not found.'
                }
                , status=status.HTTP_404_NOT_FOUND
            )
        user_like.delete()
        return Response(
                {
                    'detail': '{}, your like has been deleted successfully.'
                    .format(request.user.username)
                }
                , status=status.HTTP_200_OK
            )


class ReportArticlesView(ListCreateAPIView):
    queryset = ReportArticles.objects.all()
    serializer_class = ReportArticlesSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def post(self, request, slug):
        # Checks if there is an article with that slug
        article = get_article(slug=slug)
        if isinstance(article, dict):
            # if the article does not exist an error is returned
            return Response(article, status=status.HTTP_404_NOT_FOUND)
        if article:
            # checks if the author is trying to report the article
            if article.author == request.user:
                return Response(
                    {"errors": "You cannot report your own article"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # gets the article, user and report_msg
                article_report = article
                user_report = request.user
                report_msg = request.data.get('report', {}).get('report_msg', {})
                no_of_reports = ReportArticles.objects.filter(
                    article=article_report, user=user_report
                ).count()
                # checks how many times users has reported and returns an error
                if no_of_reports > 2:
                    return Response(
                        {"errors": "You cannot report this article multiple times"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                report = {
                    'article': article.slug,
                    'user': request.user,
                    'report_msg': report_msg
                }
                # creates an instance of the report
                serializer = self.serializer_class(data=report)
                serializer.is_valid(raise_exception=True)
                # Send mail to Admin before saving the serialized object
                current_domain = settings.DEFAULT_DOMAIN
                url = current_domain + "/api/verify/" + str(article.slug)
                email = os.getenv('ADMIN_EMAIL')
                body = render_to_string('report.html', {
                    'link': url,
                    'name': request.user.username,
                    'report': report_msg
                })
                send_mail(
                    'A user has reported an article',
                    'View reported article',
                    'no-reply@authors-heaven.com',
                    [email],
                    html_message=body,
                    fail_silently=False,
                )
                content = "An email has been sent to the admin with your request"
                message = {"message": content}
                serializer.save()
                return Response(message, status=status.HTTP_200_OK)



