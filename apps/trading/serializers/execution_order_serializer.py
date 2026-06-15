from rest_framework import serializers

from apps.trading.models import ExecutionOrder
from lib.network.oanda.data.models import Order


class ExecutionOrderSerializer(serializers.ModelSerializer):

	class Meta:
		model = ExecutionOrder
		fields = ("type", "action", "units", "price", "stop_loss", "take_profit", "base_currency", "quote_currency")
