import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Profile from './pages/Profile';
import { Toaster } from './components/ui/sonner';
import './App.css';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/profile/:handle" element={<Profile />} />
        </Routes>
        <Toaster />
      </div>
    </Router>
  );
}