from django.urls import path

from .views import CreateRecursiveStraddleOrderView


urlpatterns = [
	path("recursive-straddle/create/", CreateRecursiveStraddleOrderView.as_view())
]

