import React from 'react';
import { Card } from './ui/card';
import { Bell, BarChart3, Users, Zap, Shield, Code2 } from 'lucide-react';

export const FeaturesSection = () => {
  const features = [
    {
      icon: Users,
      title: 'Follow Top Coders',
      description: 'Track ranked programmers from Codeforces and stay updated with their performance and achievements.',
    },
    {
      icon: Bell,
      title: 'Real-time Notifications',
      description: 'Get instant alerts when your followed coders participate in contests or achieve new ranks.',
    },
    {
      icon: BarChart3,
      title: 'Performance Analytics',
      description: 'Deep dive into detailed statistics, rating graphs, and problem-solving patterns.',
    },
    {
      icon: Zap,
      title: 'Contest Insights',
      description: 'Access comprehensive contest data, solutions, and performance comparisons.',
    },
    {
      icon: Code2,
      title: 'Solution Library',
      description: 'Browse through curated solutions from top-rated competitive programmers.',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Your data is encrypted and protected with enterprise-grade security measures.',
    },
  ];

  return (
    <section id="features" className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 grid-pattern opacity-20"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Powerful Features</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Everything You Need to
            <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Excel in Competitive Programming
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Our platform provides comprehensive tools to help you track, learn, and improve your coding skills.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card
                key={index}
                className="group relative glass-card hover:border-primary/50 transition-all duration-300 p-6 sm:p-8 hover:scale-105"
              >
                {/* Hover glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl"></div>
                
                <div className="relative flex flex-col h-full">
                  <div className="mb-4">
                    <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 group-hover:scale-110 transition-transform duration-300">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;