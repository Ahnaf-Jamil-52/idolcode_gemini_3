import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X, LogOut, User, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user, idol, isAuthenticated, logout } = useAuth();
  const canAccessDashboard = isAuthenticated && !!idol;
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Home', href: '#home' },
    { name: 'Features', href: '#features' },
    { name: 'FAQ', href: '#faq' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'glass-card shadow-lg' : ''
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
              <div className="relative w-10 h-10 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center font-bold text-lg font-mono">
                <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">&lt;i&gt;</span>
              </div>
            </div>
            <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              Idolcode
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-foreground/80 hover:text-foreground transition-colors text-sm font-medium relative group"
              >
                {link.name}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-primary to-accent group-hover:w-full transition-all duration-300"></span>
              </a>
            ))}
          </div>

          {/* Dashboard Button */}
          <div className="hidden md:flex items-center">
            <Button
              variant="ghost"
              disabled={!canAccessDashboard}
              onClick={() => canAccessDashboard && navigate(`/dashboard/${idol.handle}`)}
              className={`relative group ${
                canAccessDashboard
                  ? 'text-foreground hover:text-primary hover:bg-primary/10 cursor-pointer'
                  : 'text-foreground/30 cursor-not-allowed opacity-50'
              }`}
              title={!isAuthenticated ? 'Login to access Dashboard' : !idol ? 'Select an idol to access Dashboard' : `Go to Dashboard (${idol.handle})`}
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
          </div>

          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full glass-card border border-primary/30">
                  <User className="w-4 h-4 text-primary" />
                  <span className="text-sm text-foreground font-medium">{user?.handle}</span>
                </div>
                <Button
                  variant="ghost"
                  onClick={handleLogout}
                  className="text-foreground hover:text-red-400 hover:bg-red-500/10"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/login')}
                  className="text-foreground hover:text-primary hover:bg-primary/10"
                >
                  Login
                </Button>
                <Button 
                  onClick={() => navigate('/login')}
                  className="bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-105 transition-all"
                >
                  Register
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-muted transition-colors"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 space-y-4 border-t border-border animate-in slide-in-from-top duration-300">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="block text-foreground/80 hover:text-foreground transition-colors py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {link.name}
              </a>
            ))}
            {/* Mobile Dashboard Button */}
            <Button
              variant="ghost"
              disabled={!canAccessDashboard}
              onClick={() => {
                if (canAccessDashboard) {
                  navigate(`/dashboard/${idol.handle}`);
                  setIsMobileMenuOpen(false);
                }
              }}
              className={`w-full justify-start ${
                canAccessDashboard
                  ? 'text-foreground hover:text-primary hover:bg-primary/10'
                  : 'text-foreground/30 cursor-not-allowed opacity-50'
              }`}
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Dashboard
            </Button>

            <div className="flex flex-col space-y-2 pt-4">
              {isAuthenticated ? (
                <>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg glass-card border border-primary/30">
                    <User className="w-4 h-4 text-primary" />
                    <span className="text-sm text-foreground">{user?.handle}</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    className="w-full text-red-400"
                    onClick={() => {
                      handleLogout();
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Button 
                    variant="ghost" 
                    className="w-full"
                    onClick={() => {
                      navigate('/login');
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    Login
                  </Button>
                  <Button 
                    className="w-full bg-gradient-to-r from-primary to-accent"
                    onClick={() => {
                      navigate('/login');
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;