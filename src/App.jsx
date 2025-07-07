//import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react';
import './App.css'

import Unlock from './components/PasswordUnlock';

import Navbar from './components/Navbar';
import { Routes, Route, Link } from 'react-router-dom';
import CardAdder from './components/CardAdder';
import CardViewer from './components/CardViewer';
import CardStudy from './components/CardStudy';

import AdminPage from './pages/AdminPage';

function App() {
  const [count, setCount] = useState(0)

  useEffect(() => {
  const ensureSession = async () => {
    try {
      const res = await fetch('/api/auth/whoami', { credentials: 'include' });
      if (!res.ok) throw new Error('Session not found');
    } catch {
      console.log('Creating new session...');
      await fetch('/api/auth/start-session', { method: 'POST', credentials: 'include' });
    }
  };

  ensureSession();
  }, []);

  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-3xl mx-auto">
      <Routes>
        
        <Route path="/" element={<CardViewer />} />
        <Route path="/create" element={<CardAdder />} />
        <Route path="/study" element={<CardStudy />} />
        <Route path="/unlock" element={<Unlock />} />
        <Route path="/admin" element={<AdminPage />} />

      </Routes>
      </div>
    </>
  );
}

export default App
