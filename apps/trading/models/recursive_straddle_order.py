import uuid
from uuid import UUID

from django.db import models

from apps.core.models import Account
from .execution_order import ExecutionOrder


class RecursiveStraddleOrder(models.Model):

	id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4)
	account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
	long_order: ExecutionOrder = models.ForeignKey(ExecutionOrder, on_delete=models.CASCADE, related_name="long_order")
	short_order: ExecutionOrder = models.ForeignKey(ExecutionOrder, on_delete=models.CASCADE, related_name="short_order")
	units_multiplier: float = models.FloatField(default=1.0)
	max_units: float = models.FloatField(null=True, default=None)
	orders_placed: int = models.IntegerField(default=0.0)
	is_active: bool = models.BooleanField(default=True)

	@property
	def recursions(self) -> int:
		return self.orders_placed - 2

	def increment_orders_placed(self):
		self.orders_placed += 1
		self.save()

	def __str__(self):
		field_values = [
			f"{field.name}={getattr(self, field.name)}"
			for field in self._meta.fields
		]
		return f"{self.__class__.__name__}({', '.join(field_values)})"