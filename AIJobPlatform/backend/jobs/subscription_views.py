import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required

from .models import PaymentTransaction, SubscriptionPlan, UsageLedger, UserSubscription


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValueError("Request body must be valid JSON.")


def plan_payload(plan):
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "monthly_price_inr": plan.monthly_price_inr,
        "monthly_price_usd": plan.monthly_price_usd,
        "resume_credits": plan.resume_credits,
        "ai_usage_limit": plan.ai_usage_limit,
        "job_post_limit": plan.job_post_limit,
        "features": plan.features,
    }


def ensure_subscription(user):
    plan, _ = SubscriptionPlan.objects.get_or_create(
        code=SubscriptionPlan.PlanCode.FREE,
        defaults={
            "name": "Free",
            "resume_credits": 3,
            "ai_usage_limit": 10,
            "job_post_limit": 1,
            "features": ["Basic profile", "3 resume credits", "10 AI actions"],
        },
    )
    subscription, created = UserSubscription.objects.get_or_create(
        user=user,
        defaults={
            "plan": plan,
            "resume_credits_remaining": plan.resume_credits,
            "current_period_start": timezone.now(),
            "current_period_end": timezone.now() + timedelta(days=30),
        },
    )
    if created:
        UsageLedger.objects.create(user=user, usage_type=UsageLedger.UsageType.AI, amount=0, metadata={"event": "subscription_created"})
    return subscription


def subscription_payload(subscription):
    plan = subscription.plan
    ai_remaining = max(plan.ai_usage_limit - subscription.ai_usage_count, 0)
    return {
        "plan": plan_payload(plan),
        "status": subscription.status,
        "provider": subscription.provider,
        "resume_credits_remaining": subscription.resume_credits_remaining,
        "ai_usage_count": subscription.ai_usage_count,
        "ai_usage_limit": plan.ai_usage_limit,
        "ai_usage_remaining": ai_remaining,
        "job_post_limit": plan.job_post_limit,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }


@jwt_required
@require_http_methods(["GET"])
def subscription_overview(request):
    subscription = ensure_subscription(request.user)
    plans = SubscriptionPlan.objects.filter(is_active=True)
    usage = (
        UsageLedger.objects.filter(user=request.user)
        .values("usage_type")
        .annotate(total=Count("id"))
        .order_by("usage_type")
    )
    activity = [
        {
            "type": item.usage_type,
            "amount": item.amount,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat(),
        }
        for item in UsageLedger.objects.filter(user=request.user).order_by("-created_at")[:12]
    ]
    return JsonResponse(
        {
            "subscription": subscription_payload(subscription),
            "plans": [plan_payload(plan) for plan in plans],
            "usage_summary": list(usage),
            "activity": activity,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        }
    )


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def create_checkout(request):
    try:
        payload = parse_json(request)
    except ValueError as error:
        return JsonResponse({"detail": str(error)}, status=400)

    provider = payload.get("provider", "stripe")
    plan_code = payload.get("plan", "premium")
    plan = SubscriptionPlan.objects.filter(code=plan_code, is_active=True).first()
    if not plan:
        return JsonResponse({"detail": "Plan not found."}, status=404)
    if provider not in {"stripe", "razorpay"}:
        return JsonResponse({"detail": "Provider must be stripe or razorpay."}, status=400)

    amount = plan.monthly_price_inr if provider == "razorpay" else plan.monthly_price_usd
    currency = "INR" if provider == "razorpay" else "USD"
    reference = f"{provider}_{uuid.uuid4().hex[:18]}"
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        plan=plan,
        provider=provider,
        provider_reference=reference,
        amount=amount,
        currency=currency,
        raw_response={"mode": "test_intent", "provider": provider},
    )
    return JsonResponse(
        {
            "checkout": {
                "transaction_id": transaction.id,
                "provider": provider,
                "reference": reference,
                "amount": amount,
                "currency": currency,
                "plan": plan_payload(plan),
                "stripe_price_id": plan.stripe_price_id,
                "razorpay_plan_id": plan.razorpay_plan_id,
            }
        },
        status=201,
    )


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def confirm_checkout(request):
    try:
        payload = parse_json(request)
    except ValueError as error:
        return JsonResponse({"detail": str(error)}, status=400)

    transaction = PaymentTransaction.objects.filter(id=payload.get("transaction_id"), user=request.user).first()
    if not transaction:
        return JsonResponse({"detail": "Transaction not found."}, status=404)

    transaction.status = PaymentTransaction.Status.PAID
    transaction.raw_response = {**transaction.raw_response, "confirmation": payload}
    transaction.save(update_fields=["status", "raw_response"])

    subscription = ensure_subscription(request.user)
    subscription.plan = transaction.plan
    subscription.provider = transaction.provider
    subscription.provider_subscription_id = transaction.provider_reference
    subscription.status = UserSubscription.Status.ACTIVE
    subscription.resume_credits_remaining = transaction.plan.resume_credits
    subscription.ai_usage_count = 0
    subscription.current_period_start = timezone.now()
    subscription.current_period_end = timezone.now() + timedelta(days=30)
    subscription.save()
    UsageLedger.objects.create(
        user=request.user,
        usage_type=UsageLedger.UsageType.AI,
        amount=0,
        metadata={"event": "plan_upgraded", "plan": transaction.plan.code, "provider": transaction.provider},
    )
    return JsonResponse({"subscription": subscription_payload(subscription)})


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def record_usage(request):
    subscription = ensure_subscription(request.user)
    try:
        payload = parse_json(request)
    except ValueError as error:
        return JsonResponse({"detail": str(error)}, status=400)

    usage_type = payload.get("usage_type", UsageLedger.UsageType.AI)
    amount = max(int(payload.get("amount", 1)), 1)
    if usage_type == UsageLedger.UsageType.AI and subscription.ai_usage_count + amount > subscription.plan.ai_usage_limit:
        return JsonResponse({"detail": "AI usage limit reached. Upgrade your plan to continue."}, status=402)
    if usage_type == UsageLedger.UsageType.RESUME_CREDIT and subscription.resume_credits_remaining < amount:
        return JsonResponse({"detail": "Resume credits exhausted. Upgrade or buy more credits."}, status=402)

    if usage_type == UsageLedger.UsageType.AI:
        subscription.ai_usage_count += amount
    elif usage_type == UsageLedger.UsageType.RESUME_CREDIT:
        subscription.resume_credits_remaining -= amount
    subscription.save()
    UsageLedger.objects.create(user=request.user, usage_type=usage_type, amount=amount, metadata=payload.get("metadata", {}))
    return JsonResponse({"subscription": subscription_payload(subscription)})
