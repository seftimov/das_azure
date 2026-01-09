import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .pipeline import run_pipeline


# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def onchain_sentiment_api(request):
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()

    return JsonResponse({
        "status": "started",
        "message": "Pipeline running in background"
    })
