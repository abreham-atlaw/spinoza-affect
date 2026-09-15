from rest_framework import serializers

from .execution_order_serializer import ExecutionOrderSerializer
from apps.core.serializers import AccountSerializer
from ..models import RecursiveMarketMakingOrder


class RecursiveMarketMakingOrderSerializer(serializers.ModelSerializer):

	account = AccountSerializer()
	long_order = ExecutionOrderSerializer()
	short_order = ExecutionOrderSerializer()

	class Meta:
		model = RecursiveMarketMakingOrder
		fields = (
			"id", "account", "long_order", "short_order", "units_multiplier", "max_units",
			"is_active", "max_orders"
		)
