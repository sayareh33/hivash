from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Visit(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    referer = models.CharField(max_length=500, null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    ip_hash = models.CharField(max_length=128, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    country = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    device = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)


    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_hash']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.path} at {self.timestamp}"

    @property
    def ip_address(self):
        # فقط برای نمایش در admin
        return self.ip_hash
