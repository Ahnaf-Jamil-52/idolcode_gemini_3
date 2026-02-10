import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowRight, Sparkles } from 'lucide-react';

export const CTASection = () => {
  const navigate = useNavigate();

  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 hero-pattern"></div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent"></div>
      
      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative glass-card rounded-3xl p-8 sm:p-12 lg:p-16 text-center border-2 border-primary/30 overflow-hidden">
          {/* Background Glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-accent/10 to-transparent"></div>
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-accent/20 rounded-full blur-3xl"></div>
          
          <div className="relative space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm text-muted-foreground">Start Your Journey Today</span>
            </div>
            
            {/* Heading */}
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight">
              Ready to Level Up Your
              <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Competitive Programming Skills?
              </span>
            </h2>
            
            {/* Description */}
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Follow any Codeforces coder, compare your skills, and get AI-powered problem recommendations to level up.
            </p>
            
            {/* CTA Button */}
            <div className="flex items-center justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/login')}
                className="bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] hover:scale-105 transition-all text-base sm:text-lg px-8 py-6 group"
              >
                Get Started for Free
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
            
            {/* Trust Indicators */}
            <div className="flex flex-wrap items-center justify-center gap-8 pt-8 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <span>Completely free</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-100"></div>
                <span>No sign-up required to explore</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-200"></div>
                <span>Powered by Gemini AI</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;