import React from 'react';
import { Search, UserPlus, BarChart3, TrendingUp } from 'lucide-react';

export const HowItWorks = () => {
  const steps = [
    {
      icon: Search,
      title: 'Search by Username',
      description: 'Find any Codeforces user by their username and set them as your coding idol to follow.',
      step: '01',
    },
    {
      icon: UserPlus,
      title: 'Get Recommendations',
      description: 'Receive personalized problem suggestions based on your idol\'s strengths and your areas to improve.',
      step: '02',
    },
    {
      icon: BarChart3,
      title: 'Compare & Track',
      description: 'View detailed skill comparisons across topics and track your progress over time.',
      step: '03',
    },
    {
      icon: TrendingUp,
      title: 'Level Up',
      description: 'Follow AI-guided coaching to bridge the gap between your skills and your idol\'s mastery.',
      step: '04',
    },
  ];

  return (
    <section id="how-it-works" className="relative py-20 overflow-hidden">
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