import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

const Trivia = () => {
  const [question, setQuestion] = useState('What is the capital of France?');
  const [userAnswer, setUserAnswer] = useState('');

  const handleAnswer = () => {
    // Add logic to send user's answer to the server
    // For simplicity, let's assume a successful request and update the question
    setQuestion('What is 2 + 2?');
    setUserAnswer('');
  };

  return (
    <div>
      <h1>Trivia Game</h1>
      <p>{question}</p>
      <label>
        Your Answer:
        <input type="text" value={userAnswer} onChange={(e) => setUserAnswer(e.target.value)} />
      </label>
      <button onClick={handleAnswer}>Submit Answer</button>
    </div>
  );
};

export default Trivia;
