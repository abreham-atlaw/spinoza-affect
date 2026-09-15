from requests import Request
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Account
from apps.trading.models import RecursiveMarketMakingOrder, ExecutionOrder
from apps.trading.serializers import CreateRecursiveDualOrderSerializer, RecursiveMarketMakingOrderSerializer
from di import TradingProvider


class CreateRecursiveMarketMakingOrderView(APIView):

	def post(self, request: Request) -> Response:

		serializer = CreateRecursiveDualOrderSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		order: RecursiveMarketMakingOrder = RecursiveMarketMakingOrder.objects.create(
			account=Account.objects.create(**serializer.validated_data.pop("account")),
			long_order=ExecutionOrder.objects.create(**serializer.validated_data.pop("long_order")),
			short_order=ExecutionOrder.objects.create(**serializer.validated_data.pop("short_order")),
			**serializer.validated_data,
		)

		executor = TradingProvider.provide_recursive_market_making_executor(order=order)
		executor.start()

		serializer = RecursiveMarketMakingOrderSerializer(instance=order)
		return Response(
			data=serializer.data,
			status=status.HTTP_201_CREATED
		)
