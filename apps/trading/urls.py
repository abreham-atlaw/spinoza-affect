from django.urls import path

from .views import CreateRecursiveStraddleOrderView, ListRecursiveStraddleOrdersView, CloseRecursiveStraddleOrderView

urlpatterns = [
	path("recursive-straddle/create/", CreateRecursiveStraddleOrderView.as_view()),
	path("recursive-straddle/list/", ListRecursiveStraddleOrdersView.as_view()),
	path("recursive-straddle/close/", CloseRecursiveStraddleOrderView.as_view())
]

