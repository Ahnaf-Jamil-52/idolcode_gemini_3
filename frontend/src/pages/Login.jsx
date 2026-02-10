import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { User, Lock, Loader2, ArrowRight, Code2, UserPlus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

export const Login = () => {
  const [handle, setHandle] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleAuth = async () => {
    if (!handle.trim()) {
      setValidationError('Please enter your Codeforces handle');
      return;
    }
    if (!password) {
      setValidationError('Please enter a password');
      return;
    }
    if (isRegisterMode && password.length < 4) {
      setValidationError('Password must be at least 4 characters');
      return;
    }

    setIsLoading(true);
    setValidationError('');

    try {
      const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
      const response = await axios.post(`${BACKEND_URL}${endpoint}`, {
        handle: handle.trim(),
        password,
      });

      if (response.data?.success) {
        login(response.data.handle, response.data);
        toast.success(
          isRegisterMode
            ? `Welcome to Idolcode, ${response.data.handle}!`
            : `Welcome back, ${response.data.handle}!`
        );
        navigate('/');
      }
    } catch (error) {
      const detail = error.response?.data?.detail || 'An error occurred. Please try again.';
      setValidationError(detail);
      toast.error(isRegisterMode ? 'Registration failed' : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleAuth();
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 grid-pattern opacity-30"></div>
      <div className="absolute inset-0 hero-pattern"></div>
      <div className="absolute inset-0 opacity-10"></div>

      <div className="relative z-10 w-full max-w-md mx-auto px-4">
        <div className="glass-card p-8 rounded-3xl border border-border">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center space-x-3 mb-4">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
                <div className="relative w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center font-bold text-lg font-mono">
                  <span className="text-white">&lt;i&gt;</span>
                </div>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Idolcode
              </span>
            </div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              {isRegisterMode ? 'Create Account' : 'Sign In'}
            </h1>
            <p className="text-muted-foreground">
              {isRegisterMode
                ? 'Register with your Codeforces handle'
                : 'Enter your credentials to continue'}
            </p>
          </div>

          {/* Auth Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Handle Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Codeforces Handle
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="e.g., tourist"
                  value={handle}
                  onChange={(e) => {
                    setHandle(e.target.value);
                    setValidationError('');
                  }}
                  className="pl-10 h-12 bg-background/50 border-border focus:border-primary"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder={isRegisterMode ? 'Create a password (min. 4 chars)' : 'Enter your password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setValidationError('');
                  }}
                  className="pl-10 h-12 bg-background/50 border-border focus:border-primary"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Error Message */}
            {validationError && (
              <p className="text-sm text-red-500">{validationError}</p>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-105 transition-all text-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  {isRegisterMode ? 'Registering...' : 'Signing in...'}
                </>
              ) : (
                <>
                  {isRegisterMode ? (
                    <>
                      <UserPlus className="w-5 h-5 mr-2" />
                      Register
                    </>
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </>
              )}
            </Button>
          </form>

          {/* Toggle Register / Login */}
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              {isRegisterMode ? 'Already have an account?' : "Don't have an account?"}
              <button
                type="button"
                onClick={() => {
                  setIsRegisterMode(!isRegisterMode);
                  setValidationError('');
                }}
                className="ml-1 text-primary hover:text-primary/80 font-medium transition-colors"
              >
                {isRegisterMode ? 'Sign In' : 'Register'}
              </button>
            </p>
          </div>
        </div>

        {/* Back to Home link */}
        <div className="mt-6 text-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="text-muted-foreground hover:text-foreground"
          >
            ← Back to Home
          </Button>
        </div>
      </div>
    </section>
  );
};

export default Login;
