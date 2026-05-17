from django.http import HttpResponse, JsonResponse


def api_root(request):
    if request.method == "HEAD":
        return HttpResponse(status=200)

    return JsonResponse(
        {
            "message": "AI Job Platform API is running.",
            "available_routes": [
                "/admin/",
                "/api/auth/",
                "/api/jobs/",
            ],
        }
    )
