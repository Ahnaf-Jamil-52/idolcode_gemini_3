import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ExternalLink, TrendingUp, Loader2, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

// Rating color helper (same as Dashboard)
const getRatingColor = (rating) => {
    if (!rating) return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30' };
    if (rating >= 3000) return { text: 'text-red-600', bg: 'bg-red-500/20', border: 'border-red-500/30' };
    if (rating >= 2600) return { text: 'text-red-500', bg: 'bg-red-500/20', border: 'border-red-500/30' };
    if (rating >= 2400) return { text: 'text-red-400', bg: 'bg-red-400/20', border: 'border-red-400/30' };
    if (rating >= 2100) return { text: 'text-orange-500', bg: 'bg-orange-500/20', border: 'border-orange-500/30' };
    if (rating >= 1900) return { text: 'text-purple-500', bg: 'bg-purple-500/20', border: 'border-purple-500/30' };
    if (rating >= 1600) return { text: 'text-blue-500', bg: 'bg-blue-500/20', border: 'border-blue-500/30' };
    if (rating >= 1400) return { text: 'text-cyan-500', bg: 'bg-cyan-500/20', border: 'border-cyan-500/30' };
    if (rating >= 1200) return { text: 'text-green-500', bg: 'bg-green-500/20', border: 'border-green-500/30' };
    return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30' };
};

export const SmartCurriculumCard = ({ recommendations, loading, error, onProblemClick }) => {
    const navigate = useNavigate();

    if (loading) {
        return (
            <div className="glass-card p-6 rounded-2xl border border-border mb-8">
                <div className="flex items-center gap-3 mb-4">
                    <Sparkles className="w-6 h-6 text-primary animate-pulse" />
                    <h2 className="text-2xl font-bold">AI Coach is Analyzing...</h2>
                </div>
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    <span className="ml-3 text-muted-foreground">Curating personalized recommendations...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-card p-6 rounded-2xl border border-red-500/30 bg-red-500/5 mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <AlertCircle className="w-6 h-6 text-red-500" />
                    <h2 className="text-2xl font-bold text-red-500">Unable to Load Recommendations</h2>
                </div>
                <p className="text-muted-foreground">{error}</p>
            </div>
        );
    }

    if (!recommendations || recommendations.length === 0) {
        return (
            <div className="glass-card p-6 rounded-2xl border border-border mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <Sparkles className="w-6 h-6 text-primary" />
                    <h2 className="text-2xl font-bold">Recommended for You</h2>
                </div>
                <p className="text-muted-foreground">No recommendations available yet. Solve more problems to get personalized suggestions!</p>
            </div>
        );
    }

    return (
        <div className="glass-card p-6 rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/5 to-accent/5 mb-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-primary/20">
                        <Sparkles className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold flex items-center gap-2">
                            Recommended for You
                            <span className="text-xs px-2 py-1 rounded-full bg-primary/20 text-primary font-normal">
                                AI Curated
                            </span>
                        </h2>
                        <p className="text-sm text-muted-foreground">Personalized problems from your idol's journey</p>
                    </div>
                </div>
                <TrendingUp className="w-5 h-5 text-primary" />
            </div>

            {/* Recommendations Grid */}
            <div className="space-y-4">
                {recommendations.map((rec, index) => {
                    const ratingColor = getRatingColor(rec.rating);

                    return (
                        <div
                            key={rec.problemId}
                            className="group relative p-4 rounded-xl border border-border hover:border-primary/50 bg-background/50 hover:bg-background/80 transition-all cursor-pointer"
                            onClick={() => onProblemClick && onProblemClick(rec)}
                        >
                            {/* Problem Number Badge */}
                            <div className="absolute -left-3 -top-3 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm shadow-lg">
                                {index + 1}
                            </div>

                            <div className="flex items-start justify-between gap-4">
                                {/* Problem Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="font-semibold text-lg truncate group-hover:text-primary transition-colors">
                                            {rec.name}
                                        </h3>
                                        <span className={`text-xs px-2 py-1 rounded-full ${ratingColor.bg} ${ratingColor.text} ${ratingColor.border} border font-medium whitespace-nowrap`}>
                                            {rec.rating || 'N/A'}
                                        </span>
                                    </div>

                                    {/* Coach's Reason */}
                                    <div className="flex items-start gap-2 mb-3">
                                        <div className="mt-1 p-1 rounded bg-primary/10">
                                            <Sparkles className="w-3 h-3 text-primary" />
                                        </div>
                                        <p className="text-sm text-muted-foreground italic">
                                            <span className="font-semibold text-primary">Coach says:</span> {rec.reason}
                                        </p>
                                    </div>

                                    {/* Tags */}
                                    {rec.tags && rec.tags.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            {rec.tags.slice(0, 5).map((tag) => (
                                                <span
                                                    key={tag}
                                                    className="text-xs px-2 py-1 rounded-full bg-accent/20 text-accent-foreground"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                            {rec.tags.length > 5 && (
                                                <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">
                                                    +{rec.tags.length - 5} more
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Action Buttons */}
                                <div className="flex flex-col gap-2">
                                    <Button
                                        size="sm"
                                        variant="default"
                                        className="whitespace-nowrap"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (onProblemClick) onProblemClick(rec);
                                        }}
                                    >
                                        Start Problem
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="whitespace-nowrap"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            window.open(rec.url, '_blank');
                                        }}
                                    >
                                        <ExternalLink className="w-3 h-3 mr-1" />
                                        Codeforces
                                    </Button>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Footer Note */}
            <div className="mt-6 pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground text-center">
                    💡 These recommendations are refreshed every 24 hours based on your progress and weaknesses
                </p>
            </div>
        </div>
    );
};
