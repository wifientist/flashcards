//import React from 'react'
import { useState } from 'react'
import './App.css'

import UserLogin from './components/UserLogin';

import Navbar from './components/Navbar';
import { Routes, Route, Link } from 'react-router-dom';

import CardAdder from './components/CardAdder';
import CardViewer from './components/CardViewer';
import CardStudy from './components/CardStudy';

import AdminPage from './pages/AdminPage';

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-3xl mx-auto">
      <Routes>
        
        <Route path="/" element={<div className="text-center mt-10">Welcome to the Flashcard App!</div>} />
        <Route path="/view" element={<CardViewer />} />
        <Route path="/create" element={<CardAdder />} />
        <Route path="/study" element={<CardStudy />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/login" element={<UserLogin />} />
        
        {/* Fallback route */}
        <Route path="*" element={<div className="text-center mt-10">Page not found. <Link to="/">Go back to home</Link></div>} />

      </Routes>
      </div>
    </>
  );
}

export default App
