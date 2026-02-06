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
      answer: 'Idolcode is a platform that allows you to track and follow top competitive programmers from Codeforces. You can monitor their performance, analyze their strategies, and learn from their solutions to improve your own coding skills.',
    },
    {
      question: 'How does the following system work?',
      answer: 'Simply search for any Codeforces user by their username, and click follow. You\'ll receive real-time updates about their contest participation, rating changes, and achievements. You can manage all your followed coders from your personalized dashboard.',
    },
    {
      question: 'Is Idolcode free to use?',
      answer: 'Yes! We offer a free plan that allows you to follow up to 10 coders and access basic features. For unlimited follows and advanced analytics, you can upgrade to our Pro or Team plans.',
    },
    {
      question: 'Can I access historical data and contest results?',
      answer: 'Absolutely! Pro and Team plan users get access to comprehensive historical data, including past contest performances, rating graphs, problem-solving statistics, and solution archives.',
    },
    {
      question: 'Do you support other competitive programming platforms?',
      answer: 'Currently, we focus exclusively on Codeforces to provide the best possible experience. However, we\'re working on adding support for other platforms like LeetCode, AtCoder, and CodeChef in future updates.',
    },
    {
      question: 'How often is the data updated?',
      answer: 'Our system syncs with Codeforces in real-time. Contest results and rating updates are reflected within minutes of being published on Codeforces. You\'ll always have access to the most current information.',
    },
  ];

  return (
    <section className="relative py-20 overflow-hidden">
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

        {/* Contact CTA */}
        <div className="text-center mt-12">
          <p className="text-muted-foreground mb-4">
            Still have questions? We're here to help!
          </p>
          <a
            href="mailto:support@idolcode.com"
            className="text-primary hover:text-primary/80 transition-colors font-medium"
          >
            Contact Support →
          </a>
        </div>
      </div>
    </section>
  );
};

export default FAQSection;