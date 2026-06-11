from requests import Request
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Account
from apps.trading.models import RecursiveStraddleOrder, ExecutionOrder
from apps.trading.serializers import CreateRecursiveStraddleOrderSerializer, RecursiveStraddleOrderSerializer
from apps.trading.utils.executors import RecursiveStraddleExecutor


class CreateRecursiveStraddleOrderView(APIView):

	def post(self, request: Request) -> Response:

		serializer = CreateRecursiveStraddleOrderSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		order: RecursiveStraddleOrder = RecursiveStraddleOrder.objects.create(
			account=Account.objects.create(**serializer.validated_data["account"]),
			long_order=ExecutionOrder.objects.create(**serializer.validated_data["long_order"]),
			short_order=ExecutionOrder.objects.create(**serializer.validated_data["short_order"]),
		)

		executor = RecursiveStraddleExecutor(order=order)
		executor.start()

		serializer = RecursiveStraddleOrderSerializer(instance=order)
		return Response(
			data=serializer.data,
			status=status.HTTP_201_CREATED
		)
