from rest_framework import serializers

from .execution_order_serializer import ExecutionOrderSerializer
from apps.core.serializers import AccountSerializer
from ..models import RecursiveStraddleOrder


class RecursiveStraddleOrderSerializer(serializers.ModelSerializer):

	account = AccountSerializer()
	long_order = ExecutionOrderSerializer()
	short_order = ExecutionOrderSerializer()

	class Meta:
		model = RecursiveStraddleOrder
		fields = ("account", "long_order", "short_order", "is_active")
