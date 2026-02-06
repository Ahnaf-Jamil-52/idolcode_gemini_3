import React from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Check, Zap, Crown, Rocket } from 'lucide-react';
import { toast } from 'sonner';

export const PricingSection = () => {
  const plans = [
    {
      name: 'Free',
      icon: Zap,
      price: '$0',
      period: 'forever',
      description: 'Perfect for beginners starting their journey',
      features: [
        'Follow up to 10 coders',
        'Basic performance stats',
        'Contest notifications',
        'Community access',
        'Mobile app access',
      ],
      buttonText: 'Get Started',
      popular: false,
    },
    {
      name: 'Pro',
      icon: Crown,
      price: '$9',
      period: '/month',
      description: 'For serious competitive programmers',
      features: [
        'Follow unlimited coders',
        'Advanced analytics & insights',
        'Real-time notifications',
        'Solution library access',
        'Contest history & comparisons',
        'Priority support',
        'Export data & reports',
      ],
      buttonText: 'Upgrade to Pro',
      popular: true,
    },
    {
      name: 'Team',
      icon: Rocket,
      price: '$29',
      period: '/month',
      description: 'Best for coaching teams and organizations',
      features: [
        'Everything in Pro',
        'Team collaboration tools',
        'Custom dashboards',
        'API access',
        'White-label reports',
        'Dedicated account manager',
        'Training resources',
        'Bulk user management',
      ],
      buttonText: 'Contact Sales',
      popular: false,
    },
  ];

  const handlePlanSelect = (planName) => {
    toast.success(`Selected ${planName} plan! Redirecting to checkout...`);
  };

  return (
    <section id="pricing" className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 hero-pattern"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
            <Crown className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Simple Pricing</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Choose Your
            <span className="ml-3 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Perfect Plan
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Start free and upgrade as you grow. All plans include core features.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 lg:gap-6">
          {plans.map((plan, index) => {
            const Icon = plan.icon;
            return (
              <Card
                key={index}
                className={`relative glass-card p-8 hover:scale-105 transition-all duration-300 flex flex-col ${
                  plan.popular
                    ? 'border-primary/50 shadow-[0_0_40px_rgba(6,182,212,0.3)]'
                    : 'hover:border-primary/50'
                }`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-primary to-accent rounded-full text-sm font-semibold shadow-lg">
                    Most Popular
                  </div>
                )}
                
                {/* Icon */}
                <div className="mb-6">
                  <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20">
                    <Icon className="w-8 h-8 text-primary" />
                  </div>
                </div>
                
                {/* Plan Name */}
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <p className="text-sm text-muted-foreground mb-6">{plan.description}</p>
                
                {/* Price */}
                <div className="mb-6">
                  <span className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                    {plan.price}
                  </span>
                  <span className="text-muted-foreground ml-2">{plan.period}</span>
                </div>
                
                {/* CTA Button */}
                <Button
                  onClick={() => handlePlanSelect(plan.name)}
                  className={`w-full mb-6 ${
                    plan.popular
                      ? 'bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]'
                      : 'bg-muted hover:bg-muted/80 text-foreground'
                  }`}
                >
                  {plan.buttonText}
                </Button>
                
                {/* Features */}
                <div className="space-y-3 flex-1">
                  {plan.features.map((feature, fIndex) => (
                    <div key={fIndex} className="flex items-start space-x-3">
                      <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </div>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>

        {/* Additional Info */}
        <div className="text-center mt-12">
          <p className="text-sm text-muted-foreground">
            All plans include 14-day money-back guarantee. No questions asked.
          </p>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;