from django.contrib import admin
from .models import Category, Tag, Article, ArticleImage, Comment

class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'publish_date')
    list_filter = ('status', 'category')
    search_fields = ('title', 'excerpt', 'body')
    inlines = [ArticleImageInline]
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'type', 'is_public', 'created_at')
    list_filter = ('is_public', 'type')
    search_fields = ('name', 'email', 'body')