from django.db import models
from cms.models.fields import PlaceholderField

class Placeholder(models.Model):
    placeholder = PlaceholderField('appcms_placeholder')
    name = models.CharField(max_length=300)
