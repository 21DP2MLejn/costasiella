import uuid

from django.db import models

# Create your models here.

class OrganizationLocation(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    archived = models.BooleanField(default=False)
    display_public = models.BooleanField(default=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
