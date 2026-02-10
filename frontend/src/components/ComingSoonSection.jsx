import React from 'react';
import { Globe } from 'lucide-react';

const platforms = [
  {
    name: 'LeetCode',
    url: 'https://leetcode.com',
    color: 'from-amber-400 to-amber-600',
    logo: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10">
        <path d="M13.483 0a1.374 1.374 0 0 0-.961.438L7.116 6.226l-3.854 4.126a5.266 5.266 0 0 0-1.209 2.104 5.35 5.35 0 0 0-.125.513 5.527 5.527 0 0 0 .062 2.362 5.83 5.83 0 0 0 .349 1.017 5.938 5.938 0 0 0 1.271 1.818l4.277 4.193.039.038c2.248 2.165 5.852 2.133 8.063-.074l2.396-2.392c.54-.54.54-1.414.003-1.955a1.378 1.378 0 0 0-1.951-.003l-2.396 2.392a3.021 3.021 0 0 1-4.205.038l-.02-.019-4.276-4.193c-.652-.64-.972-1.469-.948-2.263a2.68 2.68 0 0 1 .066-.523 2.545 2.545 0 0 1 .619-1.164L9.13 8.114c1.058-1.134 3.204-1.27 4.43-.278l3.501 2.831c.593.48 1.461.387 1.94-.207a1.384 1.384 0 0 0-.207-1.943l-3.5-2.831c-.8-.647-1.766-1.045-2.774-1.202l2.015-2.158A1.384 1.384 0 0 0 13.483 0zm-2.866 12.815a1.38 1.38 0 0 0-1.38 1.382 1.38 1.38 0 0 0 1.38 1.382H20.79a1.38 1.38 0 0 0 1.38-1.382 1.38 1.38 0 0 0-1.38-1.382z" />
      </svg>
    ),
  },
  {
    name: 'AtCoder',
    url: 'https://atcoder.jp',
    color: 'from-sky-400 to-sky-600',
    logo: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10">
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm-.8 4.8h1.6v6.4h-1.6V4.8zm-4 3.2h1.6v8h-1.6V8zm8 1.6h1.6v7.2h-1.6V9.6zm-4 3.2h1.6v5.6h-1.6v-5.6z" />
      </svg>
    ),
  },
  {
    name: 'CodeChef',
    url: 'https://codechef.com',
    color: 'from-orange-400 to-orange-600',
    logo: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10">
        <path d="M11.007.22C5.624.698 1.454 4.965.804 10.37c-.39 3.246.578 6.302 2.46 8.66.46-.6 2.18-2.596 2.4-2.84-.96-1.398-1.506-3.092-1.506-4.918 0-4.776 3.87-8.658 8.645-8.674 4.8-.015 8.7 3.84 8.7 8.637 0 1.87-.585 3.6-1.59 5.018.84.98 1.87 2.18 2.38 2.78 1.88-2.34 2.87-5.37 2.52-8.6-.548-5.12-4.4-9.32-9.36-10.076-.54-.08-1.08-.12-1.63-.12-.21 0-.42.01-.63.03l.21-.05zm4.63 6.654c-.64-.04-1.29.07-1.88.37a.238.238 0 0 0 .1.45c.66-.03 1.53.09 2.37.5.3.15.58.33.84.53.58-.52 1.08-1.12 1.08-1.12s-.92-.62-2.51-.73zm-7.27 0c-1.59.11-2.51.73-2.51.73s.49.6 1.07 1.12c.27-.2.55-.38.85-.53.84-.41 1.71-.53 2.37-.5a.238.238 0 0 0 .1-.45c-.59-.3-1.24-.41-1.88-.37zm7.95 3.3c-.13-.01-.28.01-.39.07-.29.14-.39.49-.24.77.68 1.24.52 2.67-.36 3.87-.89 1.2-2.35 1.91-3.84 1.91h-.1c-1.49-.02-2.93-.75-3.81-1.95-.86-1.2-1.01-2.63-.33-3.86.14-.29.04-.63-.24-.77-.29-.14-.63-.04-.77.24-.86 1.57-.68 3.42.42 4.95 1.08 1.47 2.85 2.37 4.72 2.4h.12c1.86-.02 3.62-.91 4.71-2.37 1.11-1.52 1.3-3.38.46-4.96-.1-.2-.27-.28-.44-.3h-.01z" />
      </svg>
    ),
  },
];

export const ComingSoonSection = () => {
  return (
    <section className="relative py-20 overflow-hidden">
      <div className="absolute inset-0 hero-pattern"></div>

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30 mb-6">
          <Globe className="w-4 h-4 text-primary" />
          <span className="text-sm text-muted-foreground">Expanding Soon</span>
        </div>

        {/* Big heading */}
        <h2 className="text-3xl sm:text-4xl lg:text-6xl font-bold leading-tight mb-4">
          Coming Soon to
          <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
            More Platforms
          </span>
        </h2>

        <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-14">
          We're bringing the Idolcode experience beyond Codeforces. Follow idols across all the platforms you love.
        </p>

        {/* Platform Cards */}
        <div className="flex flex-wrap items-center justify-center gap-8 lg:gap-12">
          {platforms.map((platform) => (
            <a
              key={platform.name}
              href={platform.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col items-center gap-3"
            >
              <div className={`relative p-5 rounded-2xl glass-card border border-border hover:border-primary/50 transition-all duration-300 hover:scale-110`}>
                {/* Glow */}
                <div className={`absolute inset-0 bg-gradient-to-br ${platform.color} opacity-0 group-hover:opacity-15 transition-opacity duration-500 rounded-2xl`}></div>
                <div className="relative text-muted-foreground group-hover:text-primary transition-colors">
                  {platform.logo}
                </div>
              </div>
              <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                {platform.name}
              </span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ComingSoonSection;
