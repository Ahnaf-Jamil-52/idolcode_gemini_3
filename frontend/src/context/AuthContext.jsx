import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

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
  };

  const selectIdol = (idolHandle, idolInfo) => {
    const idolData = { handle: idolHandle, ...idolInfo };
    setIdol(idolData);
    localStorage.setItem('idolcode_idol', JSON.stringify(idolData));
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
