from rest_framework import serializers

from apps.core.serializers import AccountSerializer
from .execution_order_serializer import ExecutionOrderSerializer


class CreateRecursiveStraddleOrderSerializer(serializers.Serializer):

	account = AccountSerializer()
	long_order = ExecutionOrderSerializer()
	short_order = ExecutionOrderSerializer()
