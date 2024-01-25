import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LobbyPage from './components/LobbyPage';
import Trivia from './components/Trivia';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/trivia-game" element={<Trivia />} />
      </Routes>
    </Router>
  );
}


export default App;

