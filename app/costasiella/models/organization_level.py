import uuid

from django.db import models

# Create your models here.

class OrganizationLevel(models.Model):
    archived = models.BooleanField(default=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
