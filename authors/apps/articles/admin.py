from django.contrib import admin

from .models import ArticlesModel, Comment
# Register your models here.

admin.site.register(ArticlesModel)
admin.site.register(Comment)
