from django.urls import path

from . import views

app_name = "articles"

urlpatterns = [
    path('articles/', views.ArticlesList.as_view(), name='articles'),
    path('articles/<slug>', views.ArticlesDetails.as_view(),  name='article-details'),
    path('articles/<slug>/comments/', views.CommentsListCreateView.as_view(), name='comments'),
    path('articles/<slug>/comments/<int:id>/', views.CommentsRetrieveUpdateDestroy.as_view(), name='comment-details'),
    path('articles/<slug>/rate/', views.RatingDetails.as_view(), name='ratings'),
    path('articles/<slug>/favourite', views.FavouriteGenericAPIView.as_view(), name="favourite"),
    path('tags/', views.TagsView.as_view(), name='tags'),
    path('articles/<slug>/like/', views.ArticlesLikesDislikes.as_view(),  name='article-like'),
    path('articles/<slug>/comments/<int:id>/like', views.CommentLikes.as_view(), name='comment-like'),
    path('articles/<slug>/report/', views.ReportArticlesView.as_view(), name='report'),
    path('articles/statistics/', views.ArticleStatsView.as_view(),  name='stats'),
    path('articles/<slug>/highlight/', views.HighlightedDetails.as_view(), name='highlighted'),
    path('articles/<slug>/highlight/<int:id>', views.HighlightedDetails.as_view(), name='highlighted'),

]
