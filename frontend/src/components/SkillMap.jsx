import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
    Target,
    Zap,
    TrendingUp,
    AlertTriangle,
    X,
    Settings2,
    ExternalLink,
    Loader2,
    AlertCircle,
    ChevronDown,
    ChevronRight,
} from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from "./ui/scroll-area";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

/* ── Vertical Bar Chart Row ── */
const BarChartComparison = ({ stats }) => {
    if (!stats || stats.length === 0) return null;

    const maxVal = Math.max(...stats.map(s => Math.max(s.user, s.idol)), 1);

    return (
        <div className="flex items-end gap-2 overflow-x-auto pb-2" style={{ minHeight: 240 }}>
            {stats.map((s) => {
                const userH = Math.max((s.user / maxVal) * 180, 4);
                const idolH = Math.max((s.idol / maxVal) * 180, 4);
                const isAhead = s.user >= s.idol;
                const gap = s.gap;
                return (
                    <div key={s.topic} className="flex flex-col items-center flex-shrink-0" style={{ minWidth: 56 }}>
                        {/* Gap badge */}
                        <div className="mb-1.5 h-5 flex items-center">
                            {gap !== 0 && (
                                <span className={`text-[9px] px-1 py-0.5 rounded font-mono font-bold ${
                                    gap > 0 ? 'text-red-300' : 'text-green-300'
                                }`}>
                                    {gap > 0 ? `−${gap}` : `+${Math.abs(gap)}`}
                                </span>
                            )}
                        </div>
                        {/* Bars */}
                        <div className="flex items-end gap-1" style={{ height: 180 }}>
                            {/* User bar */}
                            <div className="relative group">
                                <div
                                    className={`w-5 rounded-t-md transition-all duration-700 ${
                                        isAhead
                                            ? 'bg-gradient-to-t from-green-600 to-emerald-400'
                                            : 'bg-gradient-to-t from-cyan-600 to-cyan-400'
                                    }`}
                                    style={{ height: userH }}
                                />
                                <div className="absolute -top-5 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-[9px] font-mono text-cyan-300 whitespace-nowrap bg-black/80 px-1 rounded">
                                    {s.user}
                                </div>
                            </div>
                            {/* Idol bar */}
                            <div className="relative group">
                                <div
                                    className="w-5 rounded-t-md bg-gradient-to-t from-purple-700 to-purple-400 transition-all duration-700"
                                    style={{ height: idolH }}
                                />
                                <div className="absolute -top-5 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-[9px] font-mono text-purple-300 whitespace-nowrap bg-black/80 px-1 rounded">
                                    {s.idol}
                                </div>
                            </div>
                        </div>
                        {/* Label */}
                        <div className="mt-2 w-14 text-center">
                            <span className="text-[9px] text-muted-foreground leading-tight line-clamp-2 capitalize">
                                {s.topic}
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

const SkillMap = ({ userHandle, idolHandle }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [customTopics, setCustomTopics] = useState([]);
    const [isCustomizeOpen, setIsCustomizeOpen] = useState(false);
    const [tempSelectedTopics, setTempSelectedTopics] = useState([]);
    const [expandedTopics, setExpandedTopics] = useState({});
    const [customLoading, setCustomLoading] = useState(false);

    const fetchData = useCallback(async (selectedTopics = []) => {
        if (!userHandle || !idolHandle) return;
        try {
            const isCustom = selectedTopics.length > 0;
            if (isCustom) {
                setCustomLoading(true);
            } else {
                setLoading(true);
            }
            const params = selectedTopics.length > 0
                ? `?topics=${selectedTopics.join(',')}`
                : '';
            const response = await axios.get(
                `${BACKEND_URL}/api/skill-comparison/${userHandle}/${idolHandle}${params}`
            );
            setData(response.data);
            setError(null);
        } catch (err) {
            console.error("Failed to fetch skill map:", err);
            setError("Failed to load skill comparison data.");
        } finally {
            setLoading(false);
            setCustomLoading(false);
        }
    }, [userHandle, idolHandle]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleCustomizeOpen = () => {
        setTempSelectedTopics([...customTopics]);
        setIsCustomizeOpen(true);
    };

    /* Toggle a topic in the customize overlay — single handler, no double-fire */
    const handleTopicToggle = (topic) => {
        setTempSelectedTopics(prev => {
            if (prev.includes(topic)) {
                return prev.filter(t => t !== topic);
            }
            if (prev.length >= 3) return prev; // silently ignore if already 3
            return [...prev, topic];
        });
    };

    const handleCustomizeSave = () => {
        if (tempSelectedTopics.length !== 3) return;
        setCustomTopics(tempSelectedTopics);
        setIsCustomizeOpen(false);
        toast.success("Skill focus updated!");
        fetchData(tempSelectedTopics);
    };

    const handleOverlayClose = () => {
        setIsCustomizeOpen(false);
    };

    const toggleTopicExpand = (topic) => {
        setExpandedTopics(prev => ({ ...prev, [topic]: !prev[topic] }));
    };

    if (loading) {
        return (
            <div className="glass-card p-8 rounded-2xl border border-border mb-10 flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-muted-foreground">Analyzing skill metrics...</span>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="glass-card p-8 rounded-2xl border border-border mb-10 flex flex-col items-center justify-center h-64 text-muted-foreground">
                <AlertCircle className="w-8 h-8 mb-2 opacity-40" />
                <span className="text-sm">{error || "No skill data available."}</span>
                <Button variant="ghost" size="sm" className="mt-3" onClick={() => fetchData()}>
                    Retry
                </Button>
            </div>
        );
    }

    const { stats, weakestTopics, userRating, idolRatingAtComparison, allTopics } = data;
    const recommendationsToShow = weakestTopics || [];
    const customizeTagList = allTopics && allTopics.length > 0
        ? allTopics
        : stats.map(s => s.topic);

    return (
        <section className="mb-16 relative">
            {/* Section Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <Target className="w-6 h-6 text-primary" />
                        Skill Map
                    </h2>
                    <p className="text-muted-foreground text-sm">
                        Comparing your full history vs <span className="text-purple-400 font-medium">{idolHandle}</span>'s full history
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* ── LEFT: Bar Chart Stats ── */}
                <div className="lg:col-span-7 glass-card p-6 rounded-2xl border border-border bg-black/40 backdrop-blur-sm">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        Topic Analysis
                    </h3>

                    <ScrollArea className="w-full">
                        <BarChartComparison stats={stats} />
                    </ScrollArea>

                    {/* Legend */}
                    <div className="flex items-center gap-6 mt-4 pt-3 border-t border-white/5 text-[11px] text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-sm bg-gradient-to-t from-cyan-600 to-cyan-400" />
                            <span>You</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-sm bg-gradient-to-t from-purple-700 to-purple-400" />
                            <span>{idolHandle}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-sm bg-gradient-to-t from-green-600 to-emerald-400" />
                            <span>You (ahead)</span>
                        </div>
                    </div>
                </div>

                {/* ── RIGHT: Focus Areas / Recommendations ── */}
                <div className="lg:col-span-5 flex flex-col">
                    <div className="glass-card p-6 rounded-2xl border border-border flex-1 bg-black/40 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2">
                                <Zap className="w-5 h-5 text-yellow-400" />
                                Focus Areas
                            </h3>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleCustomizeOpen}
                                className="h-8 gap-1.5 border-primary/20 hover:bg-primary/10 hover:text-primary"
                            >
                                <Settings2 className="w-3.5 h-3.5" />
                                Customize
                            </Button>
                        </div>

                        <p className="text-xs text-muted-foreground mb-4">
                            {customTopics.length > 0
                                ? "Showing problems for your custom focus areas."
                                : `Top 3 weakest topics — problems ${idolHandle} solved to master these.`
                            }
                        </p>

                        {customLoading ? (
                            <div className="flex items-center justify-center py-16 text-muted-foreground">
                                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                                Updating focus areas...
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recommendationsToShow.map((item, idx) => {
                                    const isExpanded = expandedTopics[item.topic];
                                    return (
                                        <div key={`${item.topic}-${idx}`} className="border border-white/10 rounded-xl bg-white/5 overflow-hidden">
                                            <button
                                                onClick={() => toggleTopicExpand(item.topic)}
                                                className="w-full flex items-center gap-3 py-3 px-4 hover:bg-white/5 transition-colors text-left"
                                            >
                                                <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400 shrink-0">
                                                    <AlertTriangle className="w-4 h-4" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-semibold text-sm truncate capitalize">{item.topic}</div>
                                                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                                                        Gap: <span className="text-red-300 font-mono">{item.gap}</span> problems behind
                                                    </div>
                                                </div>
                                                {isExpanded
                                                    ? <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
                                                    : <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                                                }
                                            </button>
                                            {isExpanded && (
                                                <div className="px-4 pb-3 space-y-1 border-t border-white/5">
                                                    {item.problems && item.problems.length > 0 ? (
                                                        item.problems.map((prob, i) => (
                                                            <a
                                                                key={i}
                                                                href={prob.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="group block p-2.5 mt-1 rounded-lg hover:bg-white/10 transition-all border border-transparent hover:border-white/10"
                                                            >
                                                                <div className="flex items-center justify-between">
                                                                    <span className="text-sm font-medium text-foreground/80 group-hover:text-primary transition-colors truncate pr-2">
                                                                        {prob.name}
                                                                    </span>
                                                                    <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground shrink-0" />
                                                                </div>
                                                                <div className="flex items-center gap-2 mt-1.5">
                                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                                                                        prob.rating < 1200 ? 'bg-green-500/20 text-green-300' :
                                                                        prob.rating < 1600 ? 'bg-cyan-500/20 text-cyan-300' :
                                                                        prob.rating < 1900 ? 'bg-blue-500/20 text-blue-300' :
                                                                        prob.rating < 2400 ? 'bg-yellow-500/20 text-yellow-300' :
                                                                        'bg-red-500/20 text-red-300'
                                                                    }`}>
                                                                        {prob.rating || 'Unrated'}
                                                                    </span>
                                                                    <span className="text-[10px] text-muted-foreground font-mono opacity-70">
                                                                        {prob.contestId}{prob.index}
                                                                    </span>
                                                                </div>
                                                            </a>
                                                        ))
                                                    ) : (
                                                        <p className="text-xs text-muted-foreground py-3 text-center">
                                                            No matching problems found for this topic.
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                                {recommendationsToShow.length === 0 && (
                                    <div className="text-center py-12 flex flex-col items-center justify-center text-muted-foreground">
                                        <AlertCircle className="w-8 h-8 mb-2 opacity-20" />
                                        <span className="text-sm">No focus areas available yet.</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ── CUSTOMIZE OVERLAY ── */}
            {isCustomizeOpen && (
                <>
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={handleOverlayClose}
                    />
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={handleOverlayClose}>
                        <div
                            className="relative w-full max-w-md bg-[#0d1117] border border-white/10 rounded-2xl shadow-2xl shadow-black/50 p-6"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button
                                onClick={handleOverlayClose}
                                className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <h3 className="text-lg font-bold mb-1">Customize Focus Areas</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Select 3 topics you want to develop your skills on
                            </p>

                            {tempSelectedTopics.length > 0 && tempSelectedTopics.length !== 3 && (
                                <p className="text-xs text-red-400 font-medium mb-3">
                                    Please select exactly 3 topics ({tempSelectedTopics.length}/3 selected)
                                </p>
                            )}

                            <div className="border border-white/10 rounded-xl bg-black/30 overflow-hidden">
                                <ScrollArea className="h-[320px] p-3">
                                    <div className="space-y-1">
                                        {customizeTagList.map((tag) => {
                                            const isSelected = tempSelectedTopics.includes(tag);
                                            const isDisabled = !isSelected && tempSelectedTopics.length >= 3;
                                            return (
                                                <button
                                                    key={tag}
                                                    type="button"
                                                    disabled={isDisabled}
                                                    onClick={() => handleTopicToggle(tag)}
                                                    className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-colors text-left ${
                                                        isSelected
                                                            ? 'bg-primary/10 border border-primary/30'
                                                            : isDisabled
                                                                ? 'opacity-40 cursor-not-allowed border border-transparent'
                                                                : 'hover:bg-white/5 border border-transparent cursor-pointer'
                                                    }`}
                                                >
                                                    {/* Custom checkbox visual */}
                                                    <div className={`w-4.5 h-4.5 rounded-md border-2 flex items-center justify-center shrink-0 transition-colors ${
                                                        isSelected
                                                            ? 'bg-primary border-primary'
                                                            : 'border-white/30 bg-transparent'
                                                    }`}>
                                                        {isSelected && (
                                                            <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        )}
                                                    </div>
                                                    <span className="flex-1 text-sm font-medium capitalize">
                                                        {tag}
                                                    </span>
                                                </button>
                                            );
                                        })}
                                    </div>
                                </ScrollArea>
                            </div>

                            <div className="flex items-center justify-between mt-4">
                                <span className={`text-xs font-semibold ${
                                    tempSelectedTopics.length === 3 ? 'text-green-400' : 'text-red-400'
                                }`}>
                                    {tempSelectedTopics.length} / 3 selected
                                </span>
                                <div className="flex gap-2">
                                    <Button variant="ghost" size="sm" onClick={handleOverlayClose}>
                                        Cancel
                                    </Button>
                                    <Button
                                        size="sm"
                                        onClick={handleCustomizeSave}
                                        disabled={tempSelectedTopics.length !== 3}
                                        className="bg-primary text-primary-foreground hover:bg-primary/90"
                                    >
                                        OK
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </section>
    );
};

export default SkillMap;
