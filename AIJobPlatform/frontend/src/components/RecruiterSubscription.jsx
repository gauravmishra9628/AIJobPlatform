import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, X, Sparkles, Building2, Users } from 'lucide-react';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    price: 0,
    period: 'Free',
    icon: Building2,
    description: 'Perfect for small teams getting started',
    features: [
      { name: 'Post up to 5 jobs', included: true },
      { name: 'Basic candidate search', included: true },
      { name: 'Email support', included: true },
      { name: 'Basic analytics', included: true },
      { name: 'AI candidate matching', included: false },
      { name: 'Team collaboration', included: false },
      { name: 'Advanced filters', included: false },
      { name: 'Priority support', included: false },
    ],
    cta: 'Get Started',
    popular: false,
  },
  {
    id: 'pro',
    name: 'Professional',
    price: 49,
    period: '/month',
    icon: Sparkles,
    description: 'For growing teams needing more power',
    features: [
      { name: 'Post unlimited jobs', included: true },
      { name: 'Advanced candidate search', included: true },
      { name: 'Priority email support', included: true },
      { name: 'Full analytics dashboard', included: true },
      { name: 'AI candidate matching', included: true },
      { name: 'Team collaboration (5 users)', included: true },
      { name: 'Advanced filters', included: true },
      { name: 'Priority support', included: false },
    ],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 199,
    period: '/month',
    icon: Users,
    description: 'For large organizations with custom needs',
    features: [
      { name: 'Post unlimited jobs', included: true },
      { name: 'Premium candidate search', included: true },
      { name: '24/7 phone support', included: true },
      { name: 'Custom analytics', included: true },
      { name: 'AI candidate matching', included: true },
      { name: 'Unlimited team members', included: true },
      { name: 'Advanced filters', included: true },
      { name: 'Dedicated account manager', included: true },
    ],
    cta: 'Contact Sales',
    popular: false,
  },
];

export function RecruiterSubscription() {
  const [billingCycle, setBillingCycle] = useState('monthly');

  const getPrice = (plan) => {
    if (plan.price === 0) return 0;
    return billingCycle === 'yearly' ? Math.round(plan.price * 0.8) : plan.price;
  };

  return (
    <div className="py-16 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
            Choose Your Plan
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            Scale your hiring with powerful features designed for teams of all sizes
          </p>

          {/* Billing Toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span className={`text-sm ${billingCycle === 'monthly' ? 'text-gray-900 dark:text-white font-medium' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${billingCycle === 'yearly' ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
            <span className={`text-sm ${billingCycle === 'yearly' ? 'text-gray-900 dark:text-white font-medium' : 'text-gray-500'}`}>
              Yearly <span className="text-green-600 text-xs">(Save 20%)</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => {
            const Icon = plan.icon;
            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg ${
                  plan.popular ? 'ring-2 ring-blue-500 transform scale-105' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <span className="bg-blue-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="p-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      plan.popular ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-gray-100 dark:bg-gray-700'
                    }`}>
                      <Icon className={`w-6 h-6 ${plan.popular ? 'text-blue-600' : 'text-gray-600 dark:text-gray-400'}`} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">{plan.name}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{plan.description}</p>
                    </div>
                  </div>

                  <div className="mb-6">
                    <span className="text-4xl font-bold text-gray-900 dark:text-white">
                      ${getPrice(plan)}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">{plan.period}</span>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-3">
                        {feature.included ? (
                          <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                        ) : (
                          <X className="w-5 h-5 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                        )}
                        <span className={`text-sm ${feature.included ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400'}`}>
                          {feature.name}
                        </span>
                      </li>
                    ))}
                  </ul>

                  <button
                    className={`w-full py-3 px-4 rounded-xl font-medium transition-colors ${
                      plan.popular
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
                    }`}
                  >
                    {plan.cta}
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}