from django.http import JsonResponse


def api_root(request):
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
