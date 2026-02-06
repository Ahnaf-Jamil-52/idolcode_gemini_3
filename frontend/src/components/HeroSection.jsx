import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Search, TrendingUp, Users } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import ConfirmationModal from './ConfirmationModal';

export const HeroSection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCoder, setSelectedCoder] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Handle click outside dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Fetch suggestions when search query changes
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchQuery.trim().length < 2) {
        setSuggestions([]);
        setShowDropdown(false);
        return;
      }

      setIsLoading(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/api/coders/search`, {
          params: {
            query: searchQuery,
            limit: 5
          }
        });
        setSuggestions(response.data);
        setShowDropdown(response.data.length > 0);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
        setSuggestions([]);
        setShowDropdown(false);
      } finally {
        setIsLoading(false);
      }
    };

    const timeoutId = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, BACKEND_URL]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      toast.success(`Searching for: ${searchQuery}`);
      // Mock search functionality
    } else {
      toast.error('Please enter a coder username');
    }
  };

  const handleSuggestionClick = (coder) => {
    setSelectedCoder(coder);
    setShowDropdown(false);
    setShowConfirmModal(true);
  };

  const handleConfirmSelection = () => {
    setShowConfirmModal(false);
    toast.success(`${selectedCoder.handle} selected as your coding idol!`);
    // Navigate to profile page
    navigate(`/profile/${selectedCoder.handle}`);
  };

  const getRatingColor = (rating) => {
    if (!rating) return 'text-gray-400';
    if (rating >= 2400) return 'text-red-500';
    if (rating >= 2100) return 'text-orange-500';
    if (rating >= 1900) return 'text-purple-500';
    if (rating >= 1600) return 'text-blue-500';
    if (rating >= 1400) return 'text-cyan-500';
    if (rating >= 1200) return 'text-green-500';
    return 'text-gray-400';
  };

  return (
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Background Pattern */}
      <div className="absolute inset-0 grid-pattern opacity-30"></div>
      <div className="absolute inset-0 hero-pattern"></div>
      
      {/* Background Image */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/6100a3e9-50bd-415e-b52f-278e95a062af/images/71b7ee53dbcb65c9a063c355a5bb8e84ec9d2c333281422177e917d3926a5bae.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      ></div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8 text-center lg:text-left">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm text-muted-foreground">Track Top Competitive Programmers</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight animate-in fade-in slide-in-from-bottom-6 duration-700 delay-150">
              Follow Your
              <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Coding Idols
              </span>
            </h1>

            {/* Subheading */}
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto lg:mx-0 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
              Track, analyze, and learn from the best competitive programmers on Codeforces. 
              Stay updated with their contests, rankings, and achievements.
            </p>

            {/* Search Bar */}
            <form 
              onSubmit={handleSearch}
              className="max-w-xl mx-auto lg:mx-0 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-450"
            >
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-primary/30 to-accent/30 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative flex items-center glass-card rounded-2xl p-2 border-2 border-border hover:border-primary/50 transition-colors">
                  <Search className="w-5 h-5 text-muted-foreground ml-4" />
                  <Input
                    type="text"
                    placeholder="Search for coders on Codeforces..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-foreground placeholder:text-muted-foreground px-4"
                  />
                  <Button 
                    type="submit"
                    className="bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-105 transition-all rounded-xl"
                  >
                    Search
                  </Button>
                </div>
              </div>
            </form>

            {/* Quick Stats */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-6 text-sm animate-in fade-in slide-in-from-bottom-12 duration-700 delay-600">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-primary" />
                <span className="text-muted-foreground">10K+ Active Users</span>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-accent" />
                <span className="text-muted-foreground">500K+ Tracked Coders</span>
              </div>
            </div>
          </div>

          {/* Right Content - 3D Duck Mascot */}
          <div className="flex justify-center lg:justify-end animate-in fade-in slide-in-from-right duration-1000 delay-300">
            <div className="relative">
              {/* Glow Effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-primary/30 to-accent/30 blur-3xl rounded-full scale-150"></div>
              
              {/* Mascot */}
              <div className="relative animate-float">
                <img
                  src="https://static.prod-images.emergentagent.com/jobs/6100a3e9-50bd-415e-b52f-278e95a062af/images/a97cbcef4f6b4fec35bee68ae3b79a5e9d0324a1db31bac16216f84e8e7c4aff.png"
                  alt="Idolcode Duck Mascot with CP on visor"
                  className="w-64 sm:w-80 lg:w-96 h-auto drop-shadow-2xl relative z-10"
                  style={{ mixBlendMode: 'normal' }}
                />
              </div>

              {/* Floating Elements */}
              <div className="absolute -top-8 -right-8 w-20 h-20 bg-primary/20 rounded-full blur-2xl animate-pulse"></div>
              <div className="absolute -bottom-8 -left-8 w-24 h-24 bg-accent/20 rounded-full blur-2xl animate-pulse delay-1000"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-primary/50 rounded-full flex items-start justify-center p-2">
          <div className="w-1.5 h-3 bg-primary rounded-full animate-pulse"></div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;