//import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react';
import './App.css'

import Navbar from './components/Navbar';
import { Routes, Route, Link } from 'react-router-dom';
import CardAdder from './components/CardAdder';
import CardViewer from './components/CardViewer';
import CardStudy from './components/CardStudy';

function App() {
  const [count, setCount] = useState(0)

  useEffect(() => {
  const ensureSession = async () => {
    try {
      const res = await fetch('/api/whoami', { credentials: 'include' });
      if (!res.ok) throw new Error('Session not found');
    } catch {
      console.log('Creating new session...');
      await fetch('/api/start-session', { method: 'POST', credentials: 'include' });
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
      </Routes>
      </div>
    </>
  );
}

export default App
