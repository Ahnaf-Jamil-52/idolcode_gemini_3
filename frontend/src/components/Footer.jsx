import React from 'react';
import { Github } from 'lucide-react';

export const Footer = () => {
  const quickLinks = [
    { name: 'Features', href: '#features' },
    { name: 'How It Works', href: '#how-it-works' },
    { name: 'FAQ', href: '#faq' },
  ];

  return (
    <footer className="relative border-t border-border mt-20">
      <div className="absolute inset-0 grid-pattern opacity-20"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Content */}
        <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-8 mb-12">
          {/* Brand Column */}
          <div className="text-center md:text-left">
            <div className="flex items-center space-x-3 mb-4 justify-center md:justify-start">
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center font-bold text-lg font-mono">
                <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">&lt;i&gt;</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Idolcode
              </span>
            </div>
            <p className="text-sm text-muted-foreground max-w-xs">
              Follow top Codeforces coders, compare skills, and get AI-powered problem recommendations.
            </p>
          </div>

          {/* Quick Links */}
          <div className="flex items-center gap-6">
            {quickLinks.map((link, index) => (
              <a
                key={index}
                href={link.href}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* GitHub */}
          <div>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
              className="w-10 h-10 rounded-lg glass-card border border-border hover:border-primary/50 flex items-center justify-center transition-all hover:scale-110 group"
            >
              <Github className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </a>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-border">
          <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
            <p className="text-sm text-muted-foreground text-center sm:text-left">
              © {new Date().getFullYear()} Idolcode. All rights reserved.
            </p>
            <p className="text-sm text-muted-foreground text-center sm:text-right">
              Built for competitive programmers, by competitive programmers.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;