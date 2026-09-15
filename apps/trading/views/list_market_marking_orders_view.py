from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trading.models import RecursiveMarketMakingOrder
from apps.trading.serializers import RecursiveMarketMakingOrderSerializer


class ListRecursiveMarketMakingOrderView(APIView):

	def get(self, request: Request) -> Response:

		orders = RecursiveMarketMakingOrder.objects.filter(account__account_id=request.query_params.get("account_id"), is_active=True)
		serializer = RecursiveMarketMakingOrderSerializer(instance=orders, many=True)

		return Response(
			data=serializer.data,
			status=status.HTTP_200_OK
		)
