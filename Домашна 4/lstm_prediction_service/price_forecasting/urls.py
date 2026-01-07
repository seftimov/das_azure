from django.urls import path
from .views import lstm_api

urlpatterns = [
    path("api/lstm/", lstm_api),
]
