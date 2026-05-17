"""
Management command to create default subscription plans
"""
from django.core.management.base import BaseCommand
from jobs.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'code': 'free',
                'name': 'Free',
                'monthly_price_inr': 0,
                'monthly_price_usd': 0,
                'resume_credits': 3,
                'ai_usage_limit': 10,
                'job_post_limit': 1,
                'features': [
                    'Basic profile',
                    '3 resume uploads',
                    '10 AI actions/month',
                    'Basic job search',
                    'Limited job alerts',
                ],
            },
            {
                'code': 'pro',
                'name': 'Pro',
                'monthly_price_inr': 499,
                'monthly_price_usd': 6,
                'resume_credits': 15,
                'ai_usage_limit': 100,
                'job_post_limit': 5,
                'features': [
                    'Everything in Free',
                    '15 resume uploads',
                    '100 AI actions/month',
                    'Unlimited job applications',
                    'AI resume optimization',
                    'AI mock interviews',
                    'Career roadmap generator',
                    'Priority job alerts',
                    'Advanced analytics',
                ],
            },
            {
                'code': 'premium',
                'name': 'Premium',
                'monthly_price_inr': 999,
                'monthly_price_usd': 12,
                'resume_credits': 50,
                'ai_usage_limit': 500,
                'job_post_limit': 20,
                'features': [
                    'Everything in Pro',
                    '50 resume uploads',
                    '500 AI actions/month',
                    'Unlimited AI interviews',
                    'Resume review by experts',
                    '1-on-1 career coaching',
                    'Company insights',
                    'Early access to jobs',
                    'Dedicated support',
                ],
            },
            {
                'code': 'recruiter',
                'name': 'Recruiter',
                'monthly_price_inr': 2499,
                'monthly_price_usd': 30,
                'resume_credits': 0,
                'ai_usage_limit': 0,
                'job_post_limit': 999,
                'features': [
                    'Post unlimited jobs',
                    'AI candidate shortlisting',
                    'Advanced candidate search',
                    'Resume downloads',
                    'Candidate analytics',
                    'Team collaboration',
                    'Custom company branding',
                    'Priority support',
                    'API access',
                ],
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                code=plan_data['code'],
                defaults=plan_data
            )

            if created:
                self.stdout.write(f'Created: {plan.name}')
            else:
                # Update existing
                for key, value in plan_data.items():
                    setattr(plan, key, value)
                plan.save()
                self.stdout.write(f'Updated: {plan.name}')

        # Create plans with pricing IDs (these would be set in production)
        pro_plan = SubscriptionPlan.objects.filter(code='pro').first()
        if pro_plan:
            pro_plan.stripe_price_id = 'price_pro_monthly'  # Replace with actual Stripe price ID
            pro_plan.save()

        recruiter_plan = SubscriptionPlan.objects.filter(code='recruiter').first()
        if recruiter_plan:
            recruiter_plan.stripe_price_id = 'price_recruiter_monthly'
            recruiter_plan.save()

        self.stdout.write(self.style.SUCCESS('\nSubscription plans created successfully!'))