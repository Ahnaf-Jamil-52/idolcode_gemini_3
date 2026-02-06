import React from 'react';
import { Search, UserPlus, BarChart3, TrendingUp } from 'lucide-react';

export const HowItWorks = () => {
  const steps = [
    {
      icon: Search,
      title: 'Search Coders',
      description: 'Find and explore top competitive programmers from Codeforces by username or ranking.',
      step: '01',
    },
    {
      icon: UserPlus,
      title: 'Follow & Track',
      description: 'Add your favorite coders to your personalized dashboard and start tracking their journey.',
      step: '02',
    },
    {
      icon: BarChart3,
      title: 'Analyze Performance',
      description: 'Get detailed insights, statistics, and performance analytics of your followed coders.',
      step: '03',
    },
    {
      icon: TrendingUp,
      title: 'Learn & Improve',
      description: 'Study their solutions, techniques, and strategies to enhance your own coding skills.',
      step: '04',
    },
  ];

  return (
    <section className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 hero-pattern"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            How It
            <span className="ml-3 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Works
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Get started in four simple steps and begin your journey to competitive programming mastery.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={index}
                className="relative group"
              >
                {/* Connection Line (hidden on mobile, shown on desktop between steps) */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-primary/50 to-transparent"></div>
                )}
                
                <div className="relative glass-card rounded-2xl p-6 hover:border-primary/50 transition-all duration-300 hover:scale-105 text-center h-full flex flex-col">
                  {/* Step Number */}
                  <div className="absolute -top-4 -right-4 w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-sm shadow-lg">
                    {step.step}
                  </div>
                  
                  {/* Icon */}
                  <div className="mb-4 flex justify-center">
                    <div className="p-4 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 group-hover:scale-110 transition-transform duration-300">
                      <Icon className="w-8 h-8 text-primary" />
                    </div>
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed flex-1">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;