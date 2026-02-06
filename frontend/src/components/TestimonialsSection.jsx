import React from 'react';
import { Card } from './ui/card';
import { Star, Quote } from 'lucide-react';

export const TestimonialsSection = () => {
  const testimonials = [
    {
      name: 'Alex Chen',
      role: 'Candidate Master',
      rating: 'Codeforces: 1950',
      content: 'Idolcode has transformed how I approach competitive programming. Following top-rated coders and analyzing their strategies helped me improve my rating by 300 points!',
      stars: 5,
    },
    {
      name: 'Priya Sharma',
      role: 'Expert Programmer',
      rating: 'Codeforces: 1650',
      content: 'The real-time notifications and performance analytics are game-changers. I never miss when my favorite coders compete, and I learn so much from their approaches.',
      stars: 5,
    },
    {
      name: 'Michael Rodriguez',
      role: 'International Master',
      rating: 'Codeforces: 2300',
      content: 'As someone who trains others, Idolcode is invaluable. I use it to track promising talent and share insights with my students. The solution library is exceptional.',
      stars: 5,
    },
  ];

  return (
    <section className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 grid-pattern opacity-20"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
            <Star className="w-4 h-4 text-primary fill-primary" />
            <span className="text-sm text-muted-foreground">Loved by Programmers</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            What Our Users
            <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Are Saying
            </span>
          </h2>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {testimonials.map((testimonial, index) => (
            <Card
              key={index}
              className="group relative glass-card hover:border-primary/50 transition-all duration-300 p-6 sm:p-8 hover:scale-105 flex flex-col"
            >
              {/* Quote Icon */}
              <div className="absolute -top-4 -left-4 w-12 h-12 rounded-full bg-gradient-to-br from-primary/30 to-accent/30 flex items-center justify-center">
                <Quote className="w-6 h-6 text-primary" />
              </div>
              
              {/* Stars */}
              <div className="flex space-x-1 mb-4">
                {[...Array(testimonial.stars)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 text-primary fill-primary" />
                ))}
              </div>
              
              {/* Content */}
              <p className="text-muted-foreground text-sm leading-relaxed mb-6 flex-1">
                "{testimonial.content}"
              </p>
              
              {/* Author */}
              <div className="flex items-start space-x-4 pt-4 border-t border-border">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-lg">
                  {testimonial.name.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-foreground">{testimonial.name}</div>
                  <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                  <div className="text-xs text-primary mt-1">{testimonial.rating}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;