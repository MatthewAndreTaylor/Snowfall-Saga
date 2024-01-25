import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LobbyPage = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [username, setUsername] = useState('');
  const socket = new WebSocket('ws://localhost:5000');

  useEffect(() => {
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'update_players') {
        setPlayers(data.players);
      } else if (data.type === 'start_game') {
        // Navigate to the trivia game page when the 'start_game' message is received
        navigate('/trivia-game');
      }
    };

    return () => {
      socket.close();
    };
  }, [navigate]);

  const handleJoinLobby = () => {
    if (socket && players.length < 4 && username.trim() !== '') {
      socket.send(JSON.stringify({ type: 'join_lobby', username }));
      setUsername('');

      if (players.length === 3) {
        // Manually check for 3 players here; the server will handle the transition at 4 players
        socket.send(JSON.stringify({ type: 'join_lobby', username }));
      }
    } else {
      alert('Please enter a valid username and ensure the lobby is not full.');
    }
  };

  return (
    <div>
      <h1>Multiplayer Trivia</h1>
      <p>Players in the lobby: {players.join(', ')}</p>
      <label>
        Enter your username:
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
      </label>
      <button onClick={handleJoinLobby}>Submit Username</button>
    </div>
  );
};

export default LobbyPage;

