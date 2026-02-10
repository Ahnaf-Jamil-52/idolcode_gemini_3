import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Clock,
  Loader2,
  Inbox,
  ExternalLink,
} from 'lucide-react';
import { Button } from './ui/button';

/* ── Status badge config ─────────────────────────────────────────── */
const statusConfig = {
  solved: {
    icon: CheckCircle2,
    text: 'Accepted',
    className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  failed: {
    icon: XCircle,
    text: 'Wrong Answer',
    className: 'bg-red-500/15 text-red-400 border-red-500/30',
  },
  attempted: {
    icon: Clock,
    text: 'Attempted',
    className: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  },
};

/* ── Tag colour palette ──────────────────────────────────────────── */
const TAG_COLORS = [
  'bg-sky-500/10 text-sky-300',
  'bg-violet-500/10 text-violet-300',
  'bg-pink-500/10 text-pink-300',
  'bg-teal-500/10 text-teal-300',
  'bg-orange-500/10 text-orange-300',
];

/* ── Rating colour ───────────────────────────────────────────────── */
const getRatingColor = (rating) => {
  if (!rating) return 'text-gray-400';
  if (rating >= 2400) return 'text-red-400';
  if (rating >= 2100) return 'text-orange-400';
  if (rating >= 1900) return 'text-violet-400';
  if (rating >= 1600) return 'text-blue-400';
  if (rating >= 1400) return 'text-cyan-400';
  if (rating >= 1200) return 'text-green-400';
  return 'text-gray-400';
};

/* ── Time-ago helper ─────────────────────────────────────────────── */
const timeAgo = (isoString) => {
  if (!isoString) return '';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 30) return `${days}d ago`;
    return date.toLocaleDateString();
  } catch {
    return '';
  }
};

/* ── Single history row ──────────────────────────────────────────── */
const HistoryRow = ({ attempt, onRetry }) => {
  const navigate = useNavigate();
  const cfg = statusConfig[attempt.status] || statusConfig.attempted;
  const StatusIcon = cfg.icon;

  const handleRetry = (e) => {
    e.stopPropagation();
    if (onRetry) onRetry(attempt);
    else navigate(`/workspace/${attempt.contestId}/${attempt.index}`);
  };

  return (
    <div className="group flex items-center gap-4 px-4 py-3 rounded-xl border border-border/60 bg-background/40 hover:bg-background/70 hover:border-primary/30 transition-all">
      {/* Status icon */}
      <div className={`flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-full border ${cfg.className}`}>
        <StatusIcon className="w-4.5 h-4.5" />
      </div>

      {/* Problem info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">#{attempt.problemId}</span>
          <span className={`text-xs font-bold ${getRatingColor(attempt.rating)}`}>
            {attempt.rating || '?'}
          </span>
          {attempt.difficulty && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium">
              {attempt.difficulty}
            </span>
          )}
        </div>
        <p className="text-sm font-medium text-foreground truncate mt-0.5">
          {attempt.name || 'Unknown Problem'}
        </p>
        {/* Tags (small, inline) */}
        <div className="flex flex-wrap gap-1 mt-1">
          {(attempt.tags || []).slice(0, 3).map((tag, i) => (
            <span key={tag} className={`text-[10px] px-1.5 py-0.5 rounded ${TAG_COLORS[i % TAG_COLORS.length]}`}>
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Timestamp */}
      <span className="flex-shrink-0 text-xs text-muted-foreground hidden sm:block">
        {timeAgo(attempt.attemptedAt)}
      </span>

      {/* Status badge */}
      <span className={`flex-shrink-0 items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border hidden sm:inline-flex ${cfg.className}`}>
        <StatusIcon className="w-3 h-3" />
        {cfg.text}
      </span>

      {/* Retry / Open buttons */}
      <div className="flex-shrink-0 flex items-center gap-1.5">
        {(attempt.status === 'failed' || attempt.status === 'solved') && (
          <Button
            onClick={handleRetry}
            size="sm"
            variant="outline"
            className="text-xs gap-1 border-amber-500/30 text-amber-400 hover:bg-amber-500/10 hover:text-amber-300"
          >
            <RotateCcw className="w-3 h-3" />
            Retry
          </Button>
        )}
        {attempt.status === 'attempted' && (
          <Button
            onClick={handleRetry}
            size="sm"
            variant="outline"
            className="text-xs gap-1 border-primary/30 text-primary hover:bg-primary/10"
          >
            Continue
          </Button>
        )}
        <Button
          onClick={(e) => {
            e.stopPropagation();
            window.open(
              `https://codeforces.com/problemset/problem/${attempt.contestId}/${attempt.index}`,
              '_blank',
              'noopener,noreferrer'
            );
          }}
          size="sm"
          variant="ghost"
          className="text-xs text-muted-foreground hover:text-foreground px-2"
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
};

/* ── Main Export ──────────────────────────────────────────────────── */
export const ProblemHistory = ({ history, loading, onRetry }) => {
  if (loading) {
    return (
      <div className="glass-card p-8 rounded-2xl border border-border">
        <div className="flex items-center gap-3 mb-4">
          <History className="w-6 h-6 text-primary" />
          <h2 className="text-2xl font-bold">Problem History</h2>
        </div>
        <div className="flex items-center justify-center py-12 gap-3">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <span className="text-muted-foreground">Loading history...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 sm:p-8 rounded-2xl border border-border">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-xl bg-primary/20">
          <History className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-bold">Problem History</h2>
          <p className="text-sm text-muted-foreground">
            Problems you've solved or attempted on this platform
          </p>
        </div>
      </div>

      {(!history || history.length === 0) ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="p-4 rounded-full bg-muted/30">
            <Inbox className="w-10 h-10 text-muted-foreground/50" />
          </div>
          <div>
            <p className="text-lg font-medium text-muted-foreground">
              No problems attempted yet
            </p>
            <p className="text-sm text-muted-foreground/70 mt-1 max-w-xs">
              Start solving problems from your roadmap above — your progress will appear here.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {history.map((attempt, i) => (
            <HistoryRow
              key={attempt.id || i}
              attempt={attempt}
              onRetry={onRetry}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProblemHistory;
