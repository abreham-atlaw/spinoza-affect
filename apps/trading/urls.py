from django.urls import path

from .views import (
	CreateRecursiveStraddleOrderView, ListRecursiveStraddleOrdersView, CloseRecursiveStraddleOrderView,
	CreateRecursiveMarketMakingOrderView, ListRecursiveMarketMakingOrderView, CloseRecursiveMarketMakingOrderView
)

urlpatterns = [
	path("recursive-straddle/create/", CreateRecursiveStraddleOrderView.as_view()),
	path("recursive-straddle/list/", ListRecursiveStraddleOrdersView.as_view()),
	path("recursive-straddle/close/", CloseRecursiveStraddleOrderView.as_view()),

	path("recursive-market-making/create/", CreateRecursiveMarketMakingOrderView.as_view()),
	path("recursive-market-making/list/", ListRecursiveMarketMakingOrderView.as_view()),
	path("recursive-market-making/close/", CloseRecursiveMarketMakingOrderView.as_view())

]

