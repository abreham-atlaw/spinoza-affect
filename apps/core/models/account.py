import uuid

from django.db import models


class Account(models.Model):

	id: uuid.UUID = models.UUIDField(primary_key=True, default=uuid.uuid4)
	account_id: str = models.CharField(max_length=256)
	token: str = models.TextField()
	url: str = models.CharField(max_length=512)
	streaming_url: str = models.CharField(max_length=512)
