import './App.css'

import UserLogin from './components/UserLogin';

import Navbar from './components/Navbar';
import { Routes, Route, Link, Navigate } from 'react-router-dom';

import CardsPage from './components/CardsPage';
import StudyPage from './components/StudyPage';

import AdminPage from './pages/AdminPage';
import DecksPage from './pages/DecksPage';
import FlipPage from './pages/FlipPage';
import DashboardPage from './pages/DashboardPage';
import ProposalsPage from './pages/ProposalsPage';

function App() {
  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-3xl mx-auto">
      <Routes>

        <Route path="/" element={<FlipPage />} />
        <Route path="/cards" element={<CardsPage />} />
        <Route path="/view" element={<Navigate to="/cards" replace />} />
        <Route path="/decks" element={<DecksPage />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/proposals" element={<ProposalsPage />} />
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
