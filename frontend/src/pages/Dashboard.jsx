import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { ProblemCards } from '../components/ProblemCards';
import { ProblemHistory } from '../components/ProblemHistory';
import SkillMap from '../components/SkillMap';
import axios from 'axios';
import {
  ArrowLeft,
  Trophy,
  Loader2,
  TrendingUp,
  Award,
  Code2,
  RefreshCw,
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

// Main Dashboard Component
export const Dashboard = () => {
  const { handle: idolHandle } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading: isAuthLoading, selectIdol } = useAuth();

  // State
  const [comparison, setComparison] = useState(null);
  const [isLoadingComparison, setIsLoadingComparison] = useState(true);

  // New recommendation state
  const [recommendations, setRecommendations] = useState([]);
  const [recDescription, setRecDescription] = useState('');
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [recError, setRecError] = useState(null);

  // Problem history state
  const [problemHistory, setProblemHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isCheckingSubmissions, setIsCheckingSubmissions] = useState(false);

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
      if (isAuthLoading || !user?.handle || !idolHandle) return;
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
  }, [isAuthLoading, user?.handle, idolHandle, selectIdol]);

  // Fetch topic-aligned recommendations (new engine)
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!user?.handle || !idolHandle) return;
      setIsLoadingRecs(true);
      setRecError(null);
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/recommendations/${user.handle}/${idolHandle}`
        );
        setRecommendations(response.data.recommendations || []);
        setRecDescription(response.data.description || '');
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        setRecError(
          error.response?.data?.detail ||
          'Unable to load recommendations. Please try again later.'
        );
      } finally {
        setIsLoadingRecs(false);
      }
    };
    fetchRecommendations();
  }, [user?.handle, idolHandle]);

  // Fetch problem history
  const fetchHistory = useCallback(async () => {
    if (!user?.handle) return;
    setIsLoadingHistory(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/problem-history/${user.handle}`);
      setProblemHistory(response.data.history || []);
    } catch (error) {
      console.error('Error fetching problem history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [user?.handle]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Handle solve button click — navigate to workspace (history is recorded on submit)
  const handleSolve = (problem) => {
    navigate(`/workspace/${problem.contestId}/${problem.index}`);
  };

  // Handle retry from problem history
  const handleRetry = (attempt) => {
    navigate(`/workspace/${attempt.contestId}/${attempt.index}`);
  };

  // Check Codeforces submissions and refresh cards based on difficulty
  const handleCheckSubmissions = async () => {
    if (!user?.handle || recommendations.length === 0) return;

    setIsCheckingSubmissions(true);
    try {
      // Get problem IDs from current recommendations
      const problemIds = recommendations.map(r => r.problemId).join(',');

      const response = await axios.get(
        `${BACKEND_URL}/api/check-submissions/${user.handle}?problem_ids=${problemIds}`
      );

      const submissions = response.data.submissions || {};

      // Find which problems were solved and their difficulty
      let highestSolvedDifficulty = null; // 'Easy' < 'Medium' < 'Hard'
      const difficultyOrder = { Easy: 1, Medium: 2, Hard: 3 };
      const solvedProblems = [];

      for (const rec of recommendations) {
        const sub = submissions[rec.problemId];
        if (sub && sub.solved) {
          solvedProblems.push(rec);
          const currentDiff = rec.difficulty || 'Easy';
          if (!highestSolvedDifficulty || difficultyOrder[currentDiff] > difficultyOrder[highestSolvedDifficulty]) {
            highestSolvedDifficulty = currentDiff;
          }
        }
      }

      if (!highestSolvedDifficulty) {
        toast.info('No solved problems detected in your recent Codeforces submissions.');
        setIsCheckingSubmissions(false);
        return;
      }

      // Record each solved problem to problem history
      for (const rec of solvedProblems) {
        try {
          await axios.post(`${BACKEND_URL}/api/problem-history`, {
            userHandle: user.handle,
            idolHandle: idolHandle,
            problemId: rec.problemId,
            contestId: rec.contestId,
            index: rec.index,
            name: rec.name,
            rating: rec.rating || null,
            tags: rec.tags || [],
            difficulty: rec.difficulty || '',
            status: 'solved',
          });
        } catch (err) {
          console.error('Error recording solved problem:', err);
        }
      }

      toast.success(`Detected ${solvedProblems.length} solved problem(s)! Refreshing recommendations...`);

      // Refresh recommendations based on highest solved difficulty
      // Hard → refresh all, Medium → refresh Easy+Medium, Easy → refresh only Easy
      setIsLoadingRecs(true);
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/recommendations/${user.handle}/${idolHandle}?refresh=true`
        );

        const newRecs = response.data.recommendations || [];

        if (highestSolvedDifficulty === 'Hard') {
          // Refresh all cards
          setRecommendations(newRecs);
        } else if (highestSolvedDifficulty === 'Medium') {
          // Keep Hard, refresh Easy + Medium
          const existingHard = recommendations.find(r => r.difficulty === 'Hard');
          const freshNonHard = newRecs.filter(r => r.difficulty !== 'Hard');
          const newHard = newRecs.find(r => r.difficulty === 'Hard');
          setRecommendations([
            ...freshNonHard,
            existingHard || newHard,
          ].filter(Boolean));
        } else {
          // Easy: keep Medium + Hard, refresh Easy only
          const existingMedium = recommendations.find(r => r.difficulty === 'Medium');
          const existingHard = recommendations.find(r => r.difficulty === 'Hard');
          const freshEasy = newRecs.find(r => r.difficulty === 'Easy');
          setRecommendations([
            freshEasy || newRecs[0],
            existingMedium || newRecs.find(r => r.difficulty === 'Medium'),
            existingHard || newRecs.find(r => r.difficulty === 'Hard'),
          ].filter(Boolean));
        }

        setRecDescription(response.data.description || recDescription);
      } catch (err) {
        console.error('Error refreshing recommendations:', err);
        toast.error('Failed to refresh recommendations');
      } finally {
        setIsLoadingRecs(false);
      }

      // Also refresh history
      fetchHistory();
    } catch (error) {
      console.error('Error checking submissions:', error);
      toast.error('Failed to check Codeforces submissions');
    } finally {
      setIsCheckingSubmissions(false);
    }
  };

  // Progress calculations
  const progressPercent = comparison?.progressPercent || 0;
  const isAhead = comparison?.userAhead || false;

  if (isAuthLoading) {
    return (
      <section className="relative min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="text-xl">Loading...</span>
        </div>
      </section>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <section className="relative min-h-screen overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 grid-pattern opacity-30"></div>
      <div className="absolute inset-0 hero-pattern"></div>
      <div className="absolute inset-0 opacity-5"></div>

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
          {comparison === null ? (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              Loading progress...
            </div>
          ) : isAhead ? (
            <p className="text-xl text-green-400 font-semibold">
              You've surpassed {idolHandle}! Keep pushing forward!
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

        {/* Problem Cards — AI Roadmap (Easy / Medium / Hard) */}
        <ProblemCards
          recommendations={recommendations}
          description={recDescription}
          loading={isLoadingRecs}
          error={recError}
          onSolve={handleSolve}
          onRefresh={handleCheckSubmissions}
          isRefreshing={isCheckingSubmissions}
        />

        {/* Skill Map Comparison */}
        <SkillMap
          userHandle={user?.handle || user?.username}
          idolHandle={idolHandle}
        />

        {/* Problem History Section */}
        <ProblemHistory
          history={problemHistory}
          loading={isLoadingHistory}
          onRetry={handleRetry}
        />
      </div>
    </section>
  );
};

export default Dashboard;