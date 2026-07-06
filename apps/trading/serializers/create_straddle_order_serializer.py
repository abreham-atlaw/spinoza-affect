from rest_framework import serializers

from apps.core.serializers import AccountSerializer
from .execution_order_serializer import ExecutionOrderSerializer


class CreateRecursiveStraddleOrderSerializer(serializers.Serializer):

	account = AccountSerializer()
	long_order = ExecutionOrderSerializer()
	short_order = ExecutionOrderSerializer()
	units_multiplier = serializers.FloatField(default=1.0)
	max_units = serializers.FloatField(default=None, allow_null=True)
