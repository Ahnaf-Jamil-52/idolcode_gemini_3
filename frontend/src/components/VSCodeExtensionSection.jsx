import React from 'react';
import { Monitor, Download } from 'lucide-react';
import { Button } from './ui/button';

export const VSCodeExtensionSection = () => {
  return (
    <section className="relative py-16 overflow-hidden">
      <div className="absolute inset-0 grid-pattern opacity-20"></div>

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-card rounded-2xl p-8 sm:p-12 border border-border hover:border-primary/30 transition-colors">
          <div className="flex flex-col md:flex-row items-center gap-8">
            {/* Icon */}
            <div className="flex-shrink-0">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 flex items-center justify-center">
                <Monitor className="w-10 h-10 text-blue-400" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 text-center md:text-left">
              <h3 className="text-2xl sm:text-3xl font-bold mb-2">
                Idolcode for{' '}
                <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  VS Code
                </span>
              </h3>
              <p className="text-muted-foreground max-w-lg">
                Get problem recommendations, skill comparisons, and AI coaching right inside your editor.
                Our VS Code extension brings the full Idolcode experience to your development workflow.
              </p>
            </div>

            {/* CTA */}
            <div className="flex-shrink-0">
              <Button
                variant="outline"
                className="border-blue-500/50 hover:bg-blue-500/10 hover:border-blue-400 transition-all gap-2"
                onClick={() => window.open('https://marketplace.visualstudio.com', '_blank')}
              >
                <Download className="w-4 h-4" />
                Get Extension
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default VSCodeExtensionSection;
