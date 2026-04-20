import { Routes, Route, NavLink } from 'react-router-dom';
import { Bot, FileText, MessageSquare } from 'lucide-react';
import Assistants from './pages/Assistants';
import Documents from './pages/Documents';
import Chat from './pages/Chat';

export default function App() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-logo">
          <Bot />
          GenAI-RAG
        </div>
        <nav className="app-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            <Bot size={16} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            Asistentes
          </NavLink>
          <NavLink
            to="/chat"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            <MessageSquare size={16} style={{ marginRight: 4, verticalAlign: 'middle' }} />
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
