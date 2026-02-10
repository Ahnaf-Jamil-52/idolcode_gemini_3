import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ExternalLink,
  Loader2,
  AlertCircle,
  Target,
  Zap,
  BookOpen,
  Trophy,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { Button } from './ui/button';

/* ── Rating → colour mapping ─────────────────────────────────────── */
const getRatingColor = (rating) => {
  if (!rating) return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30', label: 'Unrated' };
  if (rating >= 3000) return { text: 'text-red-600', bg: 'bg-red-500/20', border: 'border-red-500/30', label: 'Legendary' };
  if (rating >= 2600) return { text: 'text-red-500', bg: 'bg-red-500/20', border: 'border-red-500/30', label: 'Intl. GM' };
  if (rating >= 2400) return { text: 'text-red-400', bg: 'bg-red-400/20', border: 'border-red-400/30', label: 'GM' };
  if (rating >= 2100) return { text: 'text-orange-400', bg: 'bg-orange-400/20', border: 'border-orange-400/30', label: 'IM' };
  if (rating >= 1900) return { text: 'text-violet-400', bg: 'bg-violet-400/20', border: 'border-violet-400/30', label: 'Master' };
  if (rating >= 1600) return { text: 'text-blue-400', bg: 'bg-blue-400/20', border: 'border-blue-400/30', label: 'Expert' };
  if (rating >= 1400) return { text: 'text-cyan-400', bg: 'bg-cyan-400/20', border: 'border-cyan-400/30', label: 'Specialist' };
  if (rating >= 1200) return { text: 'text-green-400', bg: 'bg-green-400/20', border: 'border-green-400/30', label: 'Pupil' };
  return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30', label: 'Newbie' };
};

/* ── Difficulty badge colours ────────────────────────────────────── */
const difficultyConfig = {
  Easy: {
    gradient: 'from-emerald-500/20 to-green-600/10',
    border: 'border-emerald-500/40',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    icon: BookOpen,
    glow: 'hover:shadow-emerald-500/20',
  },
  Medium: {
    gradient: 'from-amber-500/20 to-yellow-600/10',
    border: 'border-amber-500/40',
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    icon: Target,
    glow: 'hover:shadow-amber-500/20',
  },
  Hard: {
    gradient: 'from-rose-500/20 to-red-600/10',
    border: 'border-rose-500/40',
    badge: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    icon: Zap,
    glow: 'hover:shadow-rose-500/20',
  },
};

/* ── Tag colour palette (rotated per tag) ───────────────────────── */
const TAG_COLORS = [
  'bg-sky-500/15 text-sky-300 border-sky-500/30',
  'bg-violet-500/15 text-violet-300 border-violet-500/30',
  'bg-pink-500/15 text-pink-300 border-pink-500/30',
  'bg-teal-500/15 text-teal-300 border-teal-500/30',
  'bg-orange-500/15 text-orange-300 border-orange-500/30',
  'bg-lime-500/15 text-lime-300 border-lime-500/30',
  'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30',
];

const getTagColor = (tag, index) => TAG_COLORS[index % TAG_COLORS.length];

/* ── Single Problem Card ─────────────────────────────────────────── */
const ProblemCard = ({ problem, onSolve }) => {
  const navigate = useNavigate();
  const diff = difficultyConfig[problem.difficulty] || difficultyConfig.Medium;
  const ratingColor = getRatingColor(problem.rating);
  const DiffIcon = diff.icon;

  const handleSolve = (e) => {
    e.stopPropagation();
    if (onSolve) onSolve(problem);
    else navigate(`/workspace/${problem.contestId}/${problem.index}`);
  };

  const handleViewCF = (e) => {
    e.stopPropagation();
    window.open(problem.url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div
      className={`
        relative group flex flex-col justify-between
        rounded-2xl border ${diff.border}
        bg-gradient-to-b ${diff.gradient}
        backdrop-blur-sm p-5
        transition-all duration-300
        hover:scale-[1.02] ${diff.glow} hover:shadow-lg
      `}
    >
      {/* Difficulty badge */}
      <div className="flex items-center justify-between mb-4">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border ${diff.badge}`}>
          <DiffIcon className="w-3.5 h-3.5" />
          {problem.difficulty}
        </span>
        <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full border ${ratingColor.bg} ${ratingColor.text} ${ratingColor.border}`}>
          {problem.rating || '?'}
        </span>
      </div>

      {/* Problem ID & Name */}
      <div className="mb-4">
        <p className="text-xs font-mono text-muted-foreground mb-1 tracking-wide">
          #{problem.problemId}
        </p>
        <h3 className="text-base font-semibold text-foreground leading-tight line-clamp-2 min-h-[2.5rem]">
          {problem.name}
        </h3>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap items-center gap-1.5 mb-5 min-h-[2rem]">
        {(problem.tags || []).slice(0, 4).map((tag, i) => (
          <span
            key={tag}
            className={`text-[11px] leading-none px-2.5 py-1 rounded-full border font-medium ${getTagColor(tag, i)}`}
          >
            {tag}
          </span>
        ))}
        {(problem.tags || []).length > 4 && (
          <span className="text-[11px] leading-none px-2.5 py-1 rounded-full border border-border text-muted-foreground">
            +{problem.tags.length - 4}
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 mt-auto">
        <Button
          onClick={handleSolve}
          size="sm"
          className="flex-1 h-9 bg-foreground text-background hover:bg-foreground/90 font-semibold gap-1.5 text-sm"
        >
          Solve
          <ArrowRight className="w-3.5 h-3.5" />
        </Button>
        <Button
          onClick={handleViewCF}
          size="sm"
          variant="outline"
          className="h-9 px-3 border-border/60 hover:bg-muted/50 gap-1.5 text-sm"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          CF
        </Button>
      </div>
    </div>
  );
};

/* ── Main export: ProblemCards section ────────────────────────────── */
export const ProblemCards = ({ recommendations, description, loading, error, onSolve, onRefresh, isRefreshing }) => {
  if (loading) {
    return (
      <div className="glass-card p-8 rounded-2xl border border-border mb-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-primary/20">
            <Sparkles className="w-6 h-6 text-primary animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold">
            Analyzing Your Journey...
          </h2>
        </div>
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
          <p className="text-muted-foreground text-center max-w-sm">
            Comparing your profile with your idol's journey to find the perfect problems...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-8 rounded-2xl border border-red-500/30 bg-red-500/5 mb-10">
        <div className="flex items-center gap-3 mb-3">
          <AlertCircle className="w-6 h-6 text-red-400" />
          <h2 className="text-xl font-bold text-red-400">Unable to Load Recommendations</h2>
        </div>
        <p className="text-muted-foreground text-sm">{error}</p>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="glass-card p-8 rounded-2xl border border-border mb-10">
        <div className="flex items-center gap-3 mb-3">
          <Trophy className="w-6 h-6 text-primary" />
          <h2 className="text-xl font-bold">No Recommendations Yet</h2>
        </div>
        <p className="text-muted-foreground">
          We couldn't find suitable problems right now. Try following a different idol or check back later!
        </p>
      </div>
    );
  }

  return (
    <div className="mb-10">
      {/* Section header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/20">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              Your Roadmap
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary font-normal">
                AI Curated
              </span>
            </h2>
          </div>
        </div>
        {onRefresh && (
          <Button
            onClick={onRefresh}
            variant="outline"
            size="sm"
            disabled={isRefreshing}
            className="gap-2 border-primary/30 hover:bg-primary/10 hover:border-primary/50 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Checking...' : 'Check Submissions'}
          </Button>
        )}
      </div>

      {/* 3-liner description */}
      {description && (
        <p className="text-sm text-muted-foreground mb-6 ml-[52px] max-w-2xl leading-relaxed italic">
          {description}
        </p>
      )}

      {/* Problem cards grid (3 columns) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {recommendations.map((rec) => (
          <ProblemCard key={rec.problemId} problem={rec} onSolve={onSolve} />
        ))}
      </div>
    </div>
  );
};

export default ProblemCards;
