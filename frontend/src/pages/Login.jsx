import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { User, Loader2, ArrowRight, Code2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

export const Login = () => {
  const [handle, setHandle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const validateHandle = async () => {
    if (!handle.trim()) {
      setValidationError('Please enter your Codeforces handle');
      return;
    }

    setIsLoading(true);
    setValidationError('');

    try {
      const response = await axios.get(`${BACKEND_URL}/api/user/${handle}/info`);
      
      if (response.data) {
        login(handle, response.data);
        toast.success(`Welcome, ${response.data.handle}!`);
        navigate('/');
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setValidationError('Codeforces user not found. Please check your handle.');
      } else {
        setValidationError('Error validating handle. Please try again.');
      }
      toast.error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    validateHandle();
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
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

      <div className="relative z-10 w-full max-w-md mx-auto px-4">
        <div className="glass-card p-8 rounded-3xl border border-border">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center space-x-3 mb-4">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
                <div className="relative w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center">
                  <Code2 className="w-6 h-6 text-white" />
                </div>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Idolcode
              </span>
            </div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Sign In
            </h1>
            <p className="text-muted-foreground">
              Enter your Codeforces handle to continue
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
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
              {validationError && (
                <p className="text-sm text-red-500">{validationError}</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-105 transition-all text-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  Continue
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          {/* Info */}
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              We'll verify your handle with Codeforces
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
