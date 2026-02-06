import React from 'react';
import { Users, TrendingUp, Award, Target } from 'lucide-react';

export const StatsSection = () => {
  const stats = [
    {
      icon: Users,
      value: '10K+',
      label: 'Active Users',
      color: 'from-cyan-400 to-cyan-600',
    },
    {
      icon: TrendingUp,
      value: '500K+',
      label: 'Tracked Coders',
      color: 'from-purple-400 to-purple-600',
    },
    {
      icon: Award,
      value: '1M+',
      label: 'Contests Analyzed',
      color: 'from-pink-400 to-pink-600',
    },
    {
      icon: Target,
      value: '99.9%',
      label: 'Accuracy Rate',
      color: 'from-green-400 to-green-600',
    },
  ];

  return (
    <section className="relative py-20 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div
                key={index}
                className="group relative"
              >
                {/* Glow effect on hover */}
                <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 from-primary/20 to-accent/20 blur-2xl transition-opacity duration-500 rounded-2xl"></div>
                
                <div className="relative glass-card rounded-2xl p-6 sm:p-8 hover:border-primary/50 transition-all duration-300 hover:scale-105 text-center">
                  <div className="flex flex-col items-center space-y-4">
                    <div className={`p-3 sm:p-4 rounded-xl bg-gradient-to-br ${stat.color} bg-opacity-10`}>
                      <Icon className="w-6 h-6 sm:w-8 sm:h-8 text-primary" />
                    </div>
                    <div>
                      <div className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                        {stat.value}
                      </div>
                      <div className="text-xs sm:text-sm text-muted-foreground mt-1">
                        {stat.label}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default StatsSection;