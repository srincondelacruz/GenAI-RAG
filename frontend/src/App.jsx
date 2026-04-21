import { Routes, Route, NavLink } from 'react-router-dom';
import { Sparkles, MessageSquare } from 'lucide-react';
import Assistants from './pages/Assistants';
import Documents from './pages/Documents';
import Chat from './pages/Chat';

export default function App() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-logo">
          <Sparkles />
          GenAI·RAG
        </div>
        <nav className="app-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            Asistentes
          </NavLink>
          <NavLink
            to="/chat"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            Chat
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Assistants />} />
        <Route path="/assistants/:id/documents" element={<Documents />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/chat/:assistantId" element={<Chat />} />
      </Routes>
    </div>
  );
}
