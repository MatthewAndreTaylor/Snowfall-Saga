import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [questions, setQuestions] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [score, setScore] = useState(0);

  useEffect(() => {
    // Fetch trivia questions from Flask backend
    fetch('/api/questions')
      .then(response => response.json())
      .then(data => setQuestions(data))
      .catch(error => console.error('Error fetching questions:', error));
  }, []);

  const handleAnswer = (questionId, userAnswer) => {
    const correctAnswer = questions.find(q => q.id === questionId).answer;

    setUserAnswers(prevAnswers => ({
      ...prevAnswers,
      [questionId]: userAnswer,
    }));

    if (userAnswer === correctAnswer) {
      setScore(prevScore => prevScore + 1);
    }
  };

  return (
    <div className="App">
      <h1>Trivia Game</h1>
      <p>Score: {score}</p>
      <div>
        {questions.map(question => (
          <div key={question.id}>
            <p>{question.question}</p>
            <input
              type="text"
              placeholder="Your answer"
              onChange={(e) => handleAnswer(question.id, e.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
