from rest_framework import serializers
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator

from authors import settings
from authors.apps.articles.helpers import get_time_to_read_article
from authors.apps.profiles.models import Profile
from rest_framework.validators import UniqueTogetherValidator
from .models import ArticlesModel, Rating, Comment, Favourite, Tags, LikesDislikes, CommentLike, CommentHistory, ReportArticles, ArticleStat, Highlighted
from authors.apps.profiles.serializers import ProfileSerializer
from authors.apps.articles.relations import TagsRelation


class ArticlesSerializers(serializers.ModelSerializer):
    #add return fields
    url = serializers.SerializerMethodField(read_only=True)
    facebook = serializers.SerializerMethodField(read_only=True)
    Linkedin= serializers.SerializerMethodField(read_only=True)
    twitter= serializers.SerializerMethodField(read_only=True)
    mail= serializers.SerializerMethodField(read_only=True)
    title = serializers.CharField(
        required=True,
        max_length=128,
        error_messages={
            'required': 'Title is required',
            'max_length': 'Title cannot be more than 128'
        }
    )
    description = serializers.CharField(
        required=False,
        max_length=250,
        error_messages={
            'max_length': 'Description should not be more than 250'
        }
    )
    body = serializers.CharField(
        required=True,
        error_messages={
            'required': 'Body is required'
        }
    )

    image_url = serializers.URLField(
        required=False
    )
    favourited = serializers.SerializerMethodField()

    def get_favourited(self, obj):
        try:
            favourite = Favourite.objects.get(
                user=self.context["request"].user.id, article=obj.id)
            return True
        except:
            return False

    tags = TagsRelation(many=True, required=False)

    author = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField()

    likes_count = serializers.IntegerField(
        read_only=True,
        source="likes.count"
    )

    dislikes_count = serializers.IntegerField(
        read_only=True,
        source="dislikes.count"
    )

    def get_author(self, obj):
        """This method gets the profile object for the article"""
        serializer = ProfileSerializer(
            instance=Profile.objects.get(user=obj.author))
        return serializer.data

    def get_rating(self, obj):
        """This method gets and returns the rating for the article"""

        # Get average rating
        avg_rating = Rating.objects.filter(
            article=obj.id).aggregate(Avg('rating'))

        # Check that this user is authenticated in order to include their rating,
        # if not, we return the default rating
        user = self.context["request"].user
        if user.is_authenticated:
            try:
                rating = Rating.objects.get(user=user, article=obj.id).rating
            except Rating.DoesNotExist:
                rating = None

            return {
                'avg_rating': avg_rating['rating__avg'],
                'rating': rating
            }

        return {
            'avg_rating': avg_rating['rating__avg']
        }

    def to_representation(self, instance):
        """
        overide representatiom for custom output
        """
        representation = super(ArticlesSerializers,
                               self).to_representation(instance)
        representation['time_to_read'] = get_time_to_read_article(instance)
        return representation


    def get_url(self,obj):
        request = self.context.get("request")
        return obj.api_url(request=request)

    def get_facebook(self,obj):
        request = self.context.get("request")
        return 'http://www.facebook.com/sharer.php?u='+obj.api_url(request=request)

    def get_Linkedin(self,obj):
        request = self.context.get("request")
        return 'http://www.linkedin.com/shareArticle?mini=true&amp;url='+obj.api_url(request=request)

    def get_twitter(self,obj):
        request = self.context.get("request")
        return 'https://twitter.com/share?url='+obj.api_url(request=request)+'&amp;text=Amazing Read'

    def get_mail(self,obj):
        request = self.context.get("request")
        return  'mailto:?subject=New Article Alert&body={}'.format(
                    obj.api_url(request=request))

    class Meta:
        model = ArticlesModel
        fields = (
            'title',
            'description',
            'body',
            'facebook',
            'Linkedin',
            'twitter',
            'mail',
            'slug',
            'url',
            'tags',
            'image_url',
            'author',
            'rating',
            'likes_count',
            'dislikes_count',
            'created_at',
            'updated_at',
            'favourited'
        )

    def create(self, validated_data):
        """This method creates an article instance object and adds tags to it"""
        tags = validated_data.pop('tags', [])
        # creates an article instance
        article = ArticlesModel.objects.create(**validated_data)
        # Adds tags to the article instance
        for tag in tags:
            article.tags.add(tag)
        # returns the article object
        return article


class TagSerializers(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('tag',)

    def to_representation(self, instance):
        return instance.tag


class FavouriteSerializer(serializers.ModelSerializer):
    '''serializer for favouriting'''
    class Meta:
        model = Favourite
        fields = ('article', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('article', 'user'),
                message="You have already favourited this article"
            )
        ]

class ArticleStatSerializer(serializers.ModelSerializer):
    """
    Serializer class for reading stats
    """
    slug = serializers.SlugField(read_only=True)
    view_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    def get_comment_count(self, value):
       return Comment.objects.filter(article=value).count()

    def get_view_count(self, value):
       return ArticleStat.objects.filter(article=value).count()

    class Meta:
       model = ArticlesModel
       fields = ['slug', 'title', 'view_count', 'comment_count']

class CommentsSerializers(serializers.ModelSerializer):
    body = serializers.CharField(
        max_length=200,
        required=True,
        error_messages={
            'required': 'Comments field cannot be blank'
        }
    )

    history = serializers.SerializerMethodField()

    def get_history(self, obj):
       return [
            {
                'body': history.body,
                'created_at': self.format_date(history.created_at),
            }  for history in obj.history.all()
        ]

    def format_date(self, date):
        return date.strftime('%d %b %Y %H:%M:%S')

    def to_representation(self,instance):
       """
       overide representation for custom output
       """
       threads = [
                    {

                    'id': thread.id,
                        'body': thread.body,
                        'author': thread.author.username,
                        'created_at': self.format_date(thread.created_at),
                        'replies': thread.threads.count(),
                        'comment_like_count':thread.comment_likes.count(),
                        'updated_at': self.format_date(thread.updated_at)
                    }  for thread in instance.threads.all()
                ]
    
       representation = super(CommentsSerializers, self).to_representation(instance)
       representation['created_at'] = self.format_date(instance.created_at)
       representation['updated_at'] = self.format_date(instance.updated_at)
       representation['comment_like_count']=instance.comment_likes.count()
       representation['author'] = instance.author.username
       representation['article'] = instance.article.title
       representation['reply_count'] = instance.threads.count() 
       representation['threads'] = threads
       del representation['parent']

       return representation

    class Meta:
       model = Comment
       fields = (
           'id',
           'body',
           'created_at',
           'updated_at',
           'author',
           'article',
           'parent',
           'history'
       )
        

class RatingSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(
        required=True,
        validators=[
            MinValueValidator(
                settings.RATING_MIN,
                message='Rating cannot be less than ' +
                str(settings.RATING_MIN)
            ),
            MaxValueValidator(
                settings.RATING_MAX,
                message='Rating cannot be more than ' +
                str(settings.RATING_MAX)
            )
        ],
        error_messages={
            'required': 'The rating is required'
        }
    )

    avg_rating = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField()

    def get_avg_rating(self, obj):
        avg = Rating.objects.filter(
            article=obj.article.id).aggregate(Avg('rating'))
        return avg['rating__avg']

    def get_article(self, obj):
        return obj.article.slug

    def get_rating(self, obj):
        if self.context['request'].user.is_authenticated:
            return obj
        return None

    class Meta:
        model = Rating
        fields = ('article', 'rating', 'avg_rating')


class LikesDislikesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikesDislikes
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=LikesDislikes.objects.all(),
                fields=('article', 'reader'),
                message='You have already liked this article.'
            )
        ]


class HighlightedSerializer(serializers.ModelSerializer):
    author = serializers.CharField(
        max_length=200,
        required=True,
        error_messages={
            'required': 'Author field cannot be blank'
        }
    )

    snippet = serializers.CharField(
        required=True,
        error_messages={
            'required': 'Highlighted snippet field cannot be blank'
        }
    )

    comment = serializers.CharField(
        max_length=200,
        required=False
    )

    index = serializers.IntegerField(
        required=True,
        error_messages={
            'required': 'Highlighted snippet index field cannot be blank'
        }
    )

    def to_representation(self, instance):
        """
        overide representation for custom output
        """

        representation = super(HighlightedSerializer,
                               self).to_representation(instance)
        representation.update({
            'author': instance.author.username,
            'article': instance.article.slug
        })

        return representation

    class Meta:
        model = Highlighted
        fields = ('author', 'article', 'snippet', 'comment', 'index', "id")
        validators = [
            UniqueTogetherValidator(
                queryset=Highlighted.objects.all(),
                fields=('author', 'article', 'snippet', 'index'),
                message="This highlight has already been made."
            )
        ]


class CommentHistorySerializer(serializers.ModelSerializer):
    body = serializers.CharField(
        required=True,
        max_length=200,
        error_messages={
            'required': 'Title is required',
            'max_length': 'Title cannot be more than 200 characters'
        }
    )

    class Meta:
        model = CommentHistory
        fields = ('body', 'parent', 'created_at')


class CommentsLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=CommentLike.objects.all(),
                fields = ('specific_comment','commentor'),
                message = 'You have already liked this comment.'
            )
        ]


class ReportArticlesSerializer(serializers.ModelSerializer):
    """This class adds a model serializer for reporting article"""
    class Meta:
        model = ReportArticles
        fields = ('article', 'user', 'report_msg')

