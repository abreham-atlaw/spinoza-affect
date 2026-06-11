from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trading.models import RecursiveStraddleOrder
from apps.trading.serializers import RecursiveStraddleOrderSerializer


class ListRecursiveStraddleOrdersView(APIView):

	def get(self, request: Request) -> Response:

		orders = RecursiveStraddleOrder.objects.filter(account__account_id=request.query_params.get("account_id"), is_active=True)
		serializer = RecursiveStraddleOrderSerializer(instance=orders, many=True)

		return Response(
			data=serializer.data,
			status=status.HTTP_200_OK
		)
