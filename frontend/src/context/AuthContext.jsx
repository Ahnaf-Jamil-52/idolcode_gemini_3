import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [idol, setIdol] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load from localStorage on mount
    const savedUser = localStorage.getItem('idolcode_user');
    const savedIdol = localStorage.getItem('idolcode_idol');
    
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('idolcode_user');
      }
    }
    
    if (savedIdol) {
      try {
        setIdol(JSON.parse(savedIdol));
      } catch (e) {
        localStorage.removeItem('idolcode_idol');
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = (userHandle, userInfo) => {
    const userData = { handle: userHandle, ...userInfo };
    setUser(userData);
    localStorage.setItem('idolcode_user', JSON.stringify(userData));

    // If backend returned a saved idol, restore it
    if (userInfo.idol) {
      const idolData = { handle: userInfo.idol };
      setIdol(idolData);
      localStorage.setItem('idolcode_idol', JSON.stringify(idolData));
    }
  };

  const selectIdol = (idolHandle, idolInfo) => {
    const idolData = { handle: idolHandle, ...idolInfo };
    setIdol(idolData);
    localStorage.setItem('idolcode_idol', JSON.stringify(idolData));

    // Persist idol to backend database
    if (user?.handle) {
      axios.put(`${BACKEND_URL}/api/auth/idol`, {
        handle: user.handle,
        idolHandle: idolHandle,
      }).catch(err => console.error('Failed to save idol to DB:', err));
    }
  };

  const logout = () => {
    setUser(null);
    setIdol(null);
    localStorage.removeItem('idolcode_user');
    localStorage.removeItem('idolcode_idol');
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{
      user,
      idol,
      isLoading,
      isAuthenticated,
      login,
      selectIdol,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
