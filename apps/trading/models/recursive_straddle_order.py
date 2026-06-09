from django.db import models

from apps.core.models import Account
from .execution_order import ExecutionOrder


class RecursiveStraddleOrder(models.Model):

	account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
	long_order: ExecutionOrder = models.ForeignKey(ExecutionOrder, on_delete=models.CASCADE, related_name="long_order")
	short_order: ExecutionOrder = models.ForeignKey(ExecutionOrder, on_delete=models.CASCADE, related_name="short_order")
	is_active: bool = models.BooleanField(default=True)
