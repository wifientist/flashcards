import './App.css'

import UserLogin from './components/UserLogin';

import Navbar from './components/Navbar';
import { Routes, Route, Link, Navigate } from 'react-router-dom';

import StudyPage from './components/StudyPage';

import AdminPage from './pages/AdminPage';
import ManagePage from './pages/ManagePage';
import ProfilePage from './pages/ProfilePage';
import FlipPage from './pages/FlipPage';

function App() {
  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-3xl mx-auto">
      <Routes>

        <Route path="/" element={<FlipPage />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/manage" element={<ManagePage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/admin" element={<AdminPage />} />

        {/* Legacy routes → new homes */}
        <Route path="/cards" element={<Navigate to="/manage?tab=cards" replace />} />
        <Route path="/view" element={<Navigate to="/manage?tab=cards" replace />} />
        <Route path="/decks" element={<Navigate to="/manage" replace />} />
        <Route path="/dashboard" element={<Navigate to="/profile" replace />} />
        <Route path="/proposals" element={<Navigate to="/profile?tab=proposals" replace />} />
        <Route path="/login" element={<UserLogin />} />

        {/* Fallback route */}
        <Route path="*" element={<div className="text-center mt-10">Page not found. <Link to="/">Go back to home</Link></div>} />

      </Routes>
      </div>
    </>
  );
}

export default App
