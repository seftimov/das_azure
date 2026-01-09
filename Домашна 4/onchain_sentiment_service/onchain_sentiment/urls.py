from django.urls import path
from .views import onchain_sentiment_api

urlpatterns = [
    path("api/onchain-sentiment/", onchain_sentiment_api),
]
