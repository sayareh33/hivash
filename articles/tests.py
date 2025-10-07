from django.test import TestCase

from django.test import TestCase
from .models import Article

class ArticleModelTest(TestCase):
    def test_slug_generation(self):
        a = Article.objects.create(title='یک مقاله تستی', body='متن', status='published')
        self.assertTrue(a.slug)
