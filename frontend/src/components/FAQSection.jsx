import React from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './ui/accordion';
import { HelpCircle } from 'lucide-react';

export const FAQSection = () => {
  const faqs = [
    {
      question: 'What is Idolcode?',
      answer: 'Idolcode is a platform that lets you follow any Codeforces coder as your "idol," compare your problem-solving skills against theirs, and get personalized problem recommendations to help you bridge the gap.',
    },
    {
      question: 'How do I get started?',
      answer: 'Simply create an account with your Codeforces username, search for any Codeforces user by their handle, and set them as your idol. You\'ll immediately get skill comparisons and problem suggestions.',
    },
    {
      question: 'Is Idolcode free to use?',
      answer: 'Yes! Idolcode is completely free to use. All features including skill comparisons, problem recommendations, and AI coaching are available at no cost.',
    },
    {
      question: 'What data does Idolcode use?',
      answer: 'Idolcode uses publicly available data from the Codeforces API, including user submissions, ratings, and contest history. We don\'t access any private information.',
    },
    {
      question: 'How are problems recommended?',
      answer: 'Our engine compares your solved problems with your idol\'s across different topics (DP, graphs, greedy, etc.), identifies your weakest areas, and suggests problems at the right difficulty to help you improve.',
    },
  ];

  return (
    <section id="faq" className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 grid-pattern opacity-20"></div>
      
      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
            <HelpCircle className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Have Questions?</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Frequently Asked
            <span className="ml-3 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Questions
            </span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Everything you need to know about Idolcode
          </p>
        </div>

        {/* FAQ Accordion */}
        <div className="glass-card rounded-2xl p-6 sm:p-8 border border-border">
          <Accordion type="single" collapsible className="w-full space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="border border-border/50 rounded-xl px-6 hover:border-primary/30 transition-colors"
              >
                <AccordionTrigger className="text-left hover:text-primary transition-colors py-4">
                  <span className="font-semibold">{faq.question}</span>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground pb-4">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        {/* Contact CTA removed */}
      </div>
    </section>
  );
};

export default FAQSection;