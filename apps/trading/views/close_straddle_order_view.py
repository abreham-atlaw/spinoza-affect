from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trading.models import RecursiveStraddleOrder
from apps.trading.serializers import RecursiveStraddleOrderSerializer


class CloseRecursiveStraddleOrderView(APIView):

	def post(self, request: Request) -> Response:

		order = get_object_or_404(RecursiveStraddleOrder, pk=request.query_params.get("id"), is_active=True)
		order.is_active = False
		order.save()

		serializer = RecursiveStraddleOrderSerializer(instance=order)
		return Response(
			data=serializer.data,
			status=status.HTTP_200_OK
		)
