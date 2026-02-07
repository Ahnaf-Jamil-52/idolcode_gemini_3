import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  ArrowLeft, 
  ChevronLeft, 
  ChevronRight, 
  Star, 
  Lock, 
  Trophy, 
  Target,
  Zap,
  MapPin,
  ExternalLink,
  Loader2,
  TrendingUp,
  Award,
  Code2
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// Rating color helper
const getRatingColor = (rating) => {
  if (!rating) return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30' };
  if (rating >= 3000) return { text: 'text-red-600', bg: 'bg-red-500/20', border: 'border-red-500/30', name: 'Legendary Grandmaster' };
  if (rating >= 2600) return { text: 'text-red-500', bg: 'bg-red-500/20', border: 'border-red-500/30', name: 'International Grandmaster' };
  if (rating >= 2400) return { text: 'text-red-400', bg: 'bg-red-400/20', border: 'border-red-400/30', name: 'Grandmaster' };
  if (rating >= 2100) return { text: 'text-orange-500', bg: 'bg-orange-500/20', border: 'border-orange-500/30', name: 'International Master' };
  if (rating >= 1900) return { text: 'text-purple-500', bg: 'bg-purple-500/20', border: 'border-purple-500/30', name: 'Master' };
  if (rating >= 1600) return { text: 'text-blue-500', bg: 'bg-blue-500/20', border: 'border-blue-500/30', name: 'Expert' };
  if (rating >= 1400) return { text: 'text-cyan-500', bg: 'bg-cyan-500/20', border: 'border-cyan-500/30', name: 'Specialist' };
  if (rating >= 1200) return { text: 'text-green-500', bg: 'bg-green-500/20', border: 'border-green-500/30', name: 'Pupil' };
  return { text: 'text-gray-400', bg: 'bg-gray-500/20', border: 'border-gray-500/30', name: 'Newbie' };
};

// Stat Card Component
const StatCard = ({ icon: Icon, label, userValue, idolValue, comparison }) => {
  const userColor = getRatingColor(typeof userValue === 'number' && label.includes('Rating') ? userValue : null);
  const idolColor = getRatingColor(typeof idolValue === 'number' && label.includes('Rating') ? idolValue : null);
  
  return (
    <div className="glass-card p-4 rounded-2xl border border-border hover:border-primary/30 transition-all">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-5 h-5 text-primary" />
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="flex justify-between items-end">
        <div className="text-center flex-1">
          <p className="text-xs text-muted-foreground mb-1">You</p>
          <p className={`text-2xl font-bold ${label.includes('Rating') ? userColor.text : 'text-foreground'}`}>
            {userValue?.toLocaleString() || '—'}
          </p>
        </div>
        <div className="px-3">
          <span className={`text-xs px-2 py-1 rounded-full ${comparison >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
            {comparison >= 0 ? '+' : ''}{comparison || 0}
          </span>
        </div>
        <div className="text-center flex-1">
          <p className="text-xs text-muted-foreground mb-1">Idol</p>
          <p className={`text-2xl font-bold ${label.includes('Rating') ? idolColor.text : 'text-foreground'}`}>
            {idolValue?.toLocaleString() || '—'}
          </p>
        </div>
      </div>
    </div>
  );
};

// Problem Node Component
const ProblemNode = ({ 
  problem, 
  index, 
  isCurrentView, 
  isLastSolved, 
  isLocked, 
  isSolved,
  showDetails,
  onSolve
}) => {
  const ratingColor = getRatingColor(problem?.rating);
  const isUnlocked = !isLocked && !isSolved;
  
  return (
    <div 
      className={`relative flex flex-col items-center transition-all duration-500 ${
        isCurrentView ? 'scale-110 z-10' : 'scale-100'
      }`}
      style={{ minWidth: '180px' }}
    >
      {/* "You are here" marker */}
      {isLastSolved && (
        <div className="absolute -top-16 left-1/2 -translate-x-1/2 flex flex-col items-center animate-bounce">
          <MapPin className="w-8 h-8 text-primary fill-primary/30" />
          <span className="text-xs text-primary font-semibold whitespace-nowrap bg-background/80 px-2 py-1 rounded-full border border-primary/30">
            You are here
          </span>
        </div>
      )}
      
      {/* Lock icon for locked problems */}
      {isLocked && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2">
          <Lock className="w-6 h-6 text-muted-foreground/50" />
        </div>
      )}
      
      {/* Star Node */}
      <div 
        className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
          isSolved 
            ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-[0_0_20px_rgba(34,197,94,0.5)]' 
            : isUnlocked
              ? 'bg-gradient-to-br from-primary to-accent shadow-[0_0_20px_rgba(6,182,212,0.5)] animate-pulse'
              : isLocked
                ? 'bg-muted/50 border-2 border-dashed border-muted-foreground/30'
                : 'bg-muted/30'
        }`}
      >
        <Star 
          className={`w-7 h-7 ${
            isSolved 
              ? 'text-white fill-white' 
              : isUnlocked 
                ? 'text-white fill-white/50' 
                : 'text-muted-foreground/50'
          }`} 
        />
        {isSolved && (
          <div className="absolute inset-0 rounded-full animate-ping bg-green-500/30"></div>
        )}
      </div>
      
      {/* Current view indicator (triangle) */}
      {isCurrentView && (
        <div className="mt-2">
          <div className="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[10px] border-b-primary rotate-180"></div>
        </div>
      )}
      
      {/* Problem details */}
      {showDetails && (
        <div className={`mt-4 text-center space-y-2 transition-opacity duration-300 ${isLocked ? 'opacity-40' : 'opacity-100'}`}>
          {/* Problem ID */}
          <p className={`text-sm font-mono ${isCurrentView ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
            P#{problem?.problemId || '—'}
          </p>
          
          {/* Problem Name */}
          <p className={`text-sm font-medium ${isLocked ? 'text-muted-foreground' : 'text-foreground'} line-clamp-2 max-w-[160px]`}>
            {problem?.name || 'Unknown'}
          </p>
          
          {/* Extended details for current view */}
          {isCurrentView && (
            <div className="space-y-2 mt-3">
              {/* Tags */}
              <div className="flex flex-wrap gap-1 justify-center max-w-[180px]">
                {(problem?.tags || []).slice(0, 3).map((tag, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary/50 text-muted-foreground">
                    {tag}
                  </span>
                ))}
                {(problem?.tags || []).length > 3 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-secondary/50 text-muted-foreground">
                    +{problem.tags.length - 3}
                  </span>
                )}
              </div>
              
              {/* Difficulty */}
              <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${ratingColor.bg} ${ratingColor.border} border`}>
                <Target className={`w-3 h-3 ${ratingColor.text}`} />
                <span className={`text-xs font-semibold ${ratingColor.text}`}>
                  {problem?.rating || '?'}
                </span>
              </div>
              
              {/* Idol's rating when solved */}
              {problem?.ratingAtSolve && (
                <p className="text-xs text-muted-foreground">
                  Idol's rating: <span className={getRatingColor(problem.ratingAtSolve).text}>{problem.ratingAtSolve}</span>
                </p>
              )}
              
              {/* Rank boost indicator */}
              {problem?.wasContestSolve && (
                <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-500/20 border border-yellow-500/30">
                  <Zap className="w-3 h-3 text-yellow-500" />
                  <span className="text-xs text-yellow-500 font-semibold">Rank Boost</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main Dashboard Component
export const Dashboard = () => {
  const { handle: idolHandle } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading: isAuthLoading, selectIdol } = useAuth();
  
  // State
  const [comparison, setComparison] = useState(null);
  const [journey, setJourney] = useState({ problems: [], totalProblems: 0, hasMore: false });
  const [userSolvedProblems, setUserSolvedProblems] = useState(new Set());
  const [currentViewIndex, setCurrentViewIndex] = useState(0);
  const [isLoadingComparison, setIsLoadingComparison] = useState(true);
  const [isLoadingJourney, setIsLoadingJourney] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const constellationRef = useRef(null);
  
  const LIMIT = 100;
  const VISIBLE_NODES = 5;
  
  // Check if user is logged in (wait for auth to finish loading)
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      toast.error('Please login first');
      navigate('/login', { state: { returnTo: `/dashboard/${idolHandle}` } });
    }
  }, [isAuthenticated, isAuthLoading, navigate, idolHandle]);
  
  // Fetch comparison data
  useEffect(() => {
    const fetchComparison = async () => {
      if (!user?.handle || !idolHandle) return;
      
      setIsLoadingComparison(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/api/compare/${user.handle}/${idolHandle}`);
        setComparison(response.data);
        selectIdol(idolHandle, response.data.idol);
      } catch (error) {
        console.error('Error fetching comparison:', error);
        toast.error('Error loading comparison data');
      } finally {
        setIsLoadingComparison(false);
      }
    };
    
    fetchComparison();
  }, [user?.handle, idolHandle, selectIdol]);
  
  // Fetch idol's journey
  useEffect(() => {
    const fetchJourney = async () => {
      if (!idolHandle) return;
      
      setIsLoadingJourney(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/api/idol/${idolHandle}/journey`, {
          params: { offset: 0, limit: LIMIT }
        });
        setJourney(response.data);
        setOffset(LIMIT);
      } catch (error) {
        console.error('Error fetching journey:', error);
        toast.error('Error loading idol journey');
      } finally {
        setIsLoadingJourney(false);
      }
    };
    
    fetchJourney();
  }, [idolHandle]);
  
  // Fetch user's solved problems
  useEffect(() => {
    const fetchUserSolved = async () => {
      if (!user?.handle) return;
      
      try {
        const response = await axios.get(`${BACKEND_URL}/api/user/${user.handle}/solved-problems`);
        setUserSolvedProblems(new Set(response.data.solvedProblems));
      } catch (error) {
        console.error('Error fetching user solved problems:', error);
      }
    };
    
    fetchUserSolved();
  }, [user?.handle]);
  
  // Find the last solved problem index (following journey order)
  const findLastSolvedIndex = useCallback(() => {
    let lastSolved = -1;
    for (let i = 0; i < journey.problems.length; i++) {
      if (userSolvedProblems.has(journey.problems[i].problemId)) {
        lastSolved = i;
      } else {
        // Stop at first unsolved problem to maintain order
        break;
      }
    }
    return lastSolved;
  }, [journey.problems, userSolvedProblems]);
  
  // Calculate unlocked problems (3 after last solved, maintaining order)
  const getUnlockedIndices = useCallback(() => {
    const lastSolved = findLastSolvedIndex();
    const unlocked = new Set();
    let count = 0;
    
    for (let i = lastSolved + 1; i < journey.problems.length && count < 3; i++) {
      if (!userSolvedProblems.has(journey.problems[i].problemId)) {
        unlocked.add(i);
        count++;
      }
    }
    
    return unlocked;
  }, [journey.problems, userSolvedProblems, findLastSolvedIndex]);
  
  // Load more problems
  const loadMore = async () => {
    if (!journey.hasMore || isLoadingMore) return;
    
    setIsLoadingMore(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/idol/${idolHandle}/journey`, {
        params: { offset, limit: LIMIT }
      });
      
      setJourney(prev => ({
        problems: [...prev.problems, ...response.data.problems],
        totalProblems: response.data.totalProblems,
        hasMore: response.data.hasMore
      }));
      setOffset(prev => prev + LIMIT);
    } catch (error) {
      console.error('Error loading more problems:', error);
    } finally {
      setIsLoadingMore(false);
    }
  };
  
  // Navigation handlers
  const navigateLeft = () => {
    if (currentViewIndex > 0) {
      setCurrentViewIndex(prev => Math.max(0, prev - 1));
    }
  };
  
  const navigateRight = async () => {
    if (currentViewIndex < journey.problems.length - 1) {
      setCurrentViewIndex(prev => prev + 1);
      
      // Load more if approaching end
      if (currentViewIndex >= journey.problems.length - 5 && journey.hasMore) {
        await loadMore();
      }
    }
  };
  
  // Handle solve button click
  const handleSolve = (problem) => {
    // Open Codeforces problem page in new tab
    const url = `https://codeforces.com/contest/${problem.contestId}/problem/${problem.index}`;
    window.open(url, '_blank');
  };
  
  // Initialize current view to last solved + 1 or first problem
  useEffect(() => {
    if (journey.problems.length > 0 && userSolvedProblems.size > 0) {
      const lastSolved = findLastSolvedIndex();
      setCurrentViewIndex(Math.min(lastSolved + 1, journey.problems.length - 1));
    }
  }, [journey.problems.length, userSolvedProblems, findLastSolvedIndex]);
  
  // Calculate visible problems for constellation
  const visibleStart = Math.max(0, currentViewIndex - Math.floor(VISIBLE_NODES / 2));
  const visibleEnd = Math.min(journey.problems.length, visibleStart + VISIBLE_NODES);
  const visibleProblems = journey.problems.slice(visibleStart, visibleEnd);
  
  const lastSolvedIndex = findLastSolvedIndex();
  const unlockedIndices = getUnlockedIndices();
  
  // Progress calculations
  const progressPercent = comparison?.progressPercent || 0;
  const isAhead = comparison?.userAhead || false;
  const idolRank = comparison?.idol?.rank || 'Unknown';
  
  // Check if comparison data is loaded (not just !isLoadingComparison)
  const comparisonLoaded = !isLoadingComparison && comparison !== null;
  
  if (!isAuthenticated) {
    return null;
  }
  
  return (
    <section className="relative min-h-screen overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 grid-pattern opacity-30"></div>
      <div className="absolute inset-0 hero-pattern"></div>
      <div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/6100a3e9-50bd-415e-b52f-278e95a062af/images/71b7ee53dbcb65c9a063c355a5bb8e84ec9d2c333281422177e917d3926a5bae.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      ></div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <Button
          onClick={() => navigate('/')}
          variant="ghost"
          className="mb-6 hover:bg-primary/10"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>

        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4">
            Following{' '}
            <span className="bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              {idolHandle}
            </span>
          </h1>
          {!comparisonLoaded ? (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              Loading progress...
            </div>
          ) : isAhead ? (
            <p className="text-xl text-green-400 font-semibold">
              You've already defeated {idolHandle}! 🏆
            </p>
          ) : (
            <p className="text-xl text-muted-foreground">
              You're <span className="text-primary font-bold">{progressPercent.toFixed(1)}%</span> closer to being equals
            </p>
          )}
        </div>

        {/* Stats Comparison */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
          <StatCard 
            icon={TrendingUp}
            label="Current Rating"
            userValue={comparison?.user?.rating}
            idolValue={comparison?.idol?.rating}
            comparison={(comparison?.user?.rating || 0) - (comparison?.idol?.rating || 0)}
          />
          <StatCard 
            icon={Award}
            label="Max Rating"
            userValue={comparison?.user?.maxRating}
            idolValue={comparison?.idol?.maxRating}
            comparison={(comparison?.user?.maxRating || 0) - (comparison?.idol?.maxRating || 0)}
          />
          <StatCard 
            icon={Code2}
            label="Problems Solved"
            userValue={comparison?.user?.problemsSolved}
            idolValue={comparison?.idol?.problemsSolved}
            comparison={(comparison?.user?.problemsSolved || 0) - (comparison?.idol?.problemsSolved || 0)}
          />
          <StatCard 
            icon={Trophy}
            label="Contest Wins"
            userValue={comparison?.user?.contestWins}
            idolValue={comparison?.idol?.contestWins}
            comparison={(comparison?.user?.contestWins || 0) - (comparison?.idol?.contestWins || 0)}
          />
        </div>

        {/* Problem Constellation Section */}
        <div className="glass-card p-8 rounded-3xl border border-border">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              PROBLEM CONSTELLATION
            </h2>
            <p className="text-muted-foreground">
              <span className="text-primary font-semibold">{idolHandle}</span>'s problem journey to being{' '}
              <span className={getRatingColor(comparison?.idol?.maxRating).text}>
                {comparison?.idol?.maxRank || idolRank}
              </span>
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {journey.totalProblems.toLocaleString()} problems in total
            </p>
          </div>

          {isLoadingJourney ? (
            <div className="flex items-center justify-center h-64 gap-2 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin" />
              Loading constellation...
            </div>
          ) : (
            <div className="relative">
              {/* Left Navigation Arrow */}
              <button
                onClick={navigateLeft}
                disabled={currentViewIndex === 0}
                className={`absolute left-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 flex items-center justify-center rounded-full glass-card border border-border transition-all ${
                  currentViewIndex === 0 
                    ? 'opacity-30 cursor-not-allowed' 
                    : 'hover:border-primary hover:bg-primary/10 cursor-pointer'
                }`}
              >
                <ChevronLeft className="w-6 h-6 text-primary" />
              </button>

              {/* Constellation Container */}
              <div 
                ref={constellationRef}
                className="relative overflow-hidden mx-16 py-8"
              >
                {/* Connection Line */}
                <div className="absolute top-[50%] left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-primary/50 to-transparent transform -translate-y-1/2"></div>
                
                {/* Nodes */}
                <div 
                  className="flex items-center justify-center gap-4 transition-transform duration-500 ease-out"
                  style={{ 
                    minHeight: '320px',
                  }}
                >
                  {visibleProblems.map((problem, localIndex) => {
                    const globalIndex = visibleStart + localIndex;
                    const isSolved = userSolvedProblems.has(problem.problemId);
                    const isUnlocked = unlockedIndices.has(globalIndex);
                    const isLocked = !isSolved && !isUnlocked && globalIndex > lastSolvedIndex + 3;
                    const isCurrentView = globalIndex === currentViewIndex;
                    const isLastSolved = globalIndex === lastSolvedIndex;
                    const showDetails = Math.abs(globalIndex - currentViewIndex) <= 1;
                    
                    return (
                      <ProblemNode
                        key={problem.problemId}
                        problem={problem}
                        index={globalIndex}
                        isCurrentView={isCurrentView}
                        isLastSolved={isLastSolved}
                        isLocked={isLocked}
                        isSolved={isSolved}
                        showDetails={showDetails}
                        onSolve={handleSolve}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Right Navigation Arrow */}
              <button
                onClick={navigateRight}
                disabled={currentViewIndex >= journey.problems.length - 1 && !journey.hasMore}
                className={`absolute right-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 flex items-center justify-center rounded-full glass-card border border-border transition-all ${
                  currentViewIndex >= journey.problems.length - 1 && !journey.hasMore
                    ? 'opacity-30 cursor-not-allowed' 
                    : 'hover:border-primary hover:bg-primary/10 cursor-pointer'
                }`}
              >
                <ChevronRight className="w-6 h-6 text-primary" />
              </button>
            </div>
          )}

          {/* Solve Button */}
          {!isLoadingJourney && journey.problems[currentViewIndex] && (
            <div className="text-center mt-8">
              {(() => {
                const currentProblem = journey.problems[currentViewIndex];
                const isSolved = userSolvedProblems.has(currentProblem.problemId);
                const isUnlocked = unlockedIndices.has(currentViewIndex);
                const isLocked = !isSolved && !isUnlocked && currentViewIndex > lastSolvedIndex + 3;
                
                if (isSolved) {
                  return (
                    <div className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-green-500/20 border border-green-500/30 text-green-400">
                      <Trophy className="w-5 h-5" />
                      <span className="font-semibold">Solved!</span>
                    </div>
                  );
                }
                
                if (isLocked) {
                  return (
                    <div className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-muted/50 border border-muted-foreground/30 text-muted-foreground">
                      <Lock className="w-5 h-5" />
                      <span>Solve previous problems first</span>
                    </div>
                  );
                }
                
                return (
                  <Button
                    onClick={() => handleSolve(currentProblem)}
                    className="px-8 py-6 text-lg bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] hover:scale-105 transition-all"
                  >
                    <ExternalLink className="w-5 h-5 mr-2" />
                    SOLVE!
                  </Button>
                );
              })()}
            </div>
          )}

          {/* Loading more indicator */}
          {isLoadingMore && (
            <div className="flex items-center justify-center gap-2 mt-4 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading more problems...
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default Dashboard;
