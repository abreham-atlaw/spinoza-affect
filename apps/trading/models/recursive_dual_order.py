import uuid
from uuid import UUID

from django.db import models

from apps.core.models import Account
from lib.utils.django_utils import DjangoUtils
from .execution_order import ExecutionOrder

class RecursiveDualOrder(models.Model):

	class Meta:
		abstract = True

	id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4)
	account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
	long_order: ExecutionOrder = models.ForeignKey(
		ExecutionOrder,
		on_delete=models.CASCADE,
		related_name="%(app_label)s_%(class)s_long_orders"
	)
	short_order: ExecutionOrder = models.ForeignKey(
		ExecutionOrder,
		on_delete=models.CASCADE,
		related_name="%(app_label)s_%(class)s_short_orders"
	)
	units_multiplier: float = models.FloatField(default=1.0)
	max_units: float = models.FloatField(null=True, default=None)
	max_orders: int = models.IntegerField(null=True, default=None)
	orders_placed: int = models.IntegerField(default=0.0)
	initial_units_corrected = models.BooleanField(default=False)
	is_active: bool = models.BooleanField(default=True)

	@property
	def recursions(self) -> int:
		return self.orders_placed - 2

	def increment_orders_placed(self):
		self.refresh_from_db()
		self.orders_placed += 1
		self.save()

	def deactivate(self):
		self.refresh_from_db()
		self.is_active = False
		self.save()

	def __str__(self):
		return DjangoUtils.articulate_object(self)
