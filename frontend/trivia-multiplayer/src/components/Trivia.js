import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../stylesheets/components/Trivia.css';

const Trivia = () => {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [answerChoices, setAnswerChoices] = useState([]);
  const [userAnswer, setUserAnswer] = useState('');
  const [timer, setTimer] = useState(null);
  const [countdown, setCountdown] = useState(15);

  useEffect(() => {
    // Fetch the list of questions from the Flask backend
    const fetchQuestions = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/questions');
        setQuestions(response.data); // Assuming the response is an array of questions
      } catch (error) {
        console.error('Error fetching questions:', error);
      }
    };

    fetchQuestions();
  }, []);

  useEffect(() => {
    if (timer && countdown > 0) {
      // Update the countdown every second
      const interval = setInterval(() => {
        setCountdown((prevCountdown) => prevCountdown - 1);
      }, 1000);

      return () => clearInterval(interval); // Cleanup interval on component unmount or when the timer is cleared
    } else if (timer && countdown === 0) {
      // Automatically move to the next question when the countdown reaches 0
      handleNextQuestion();
    }
  }, [countdown, timer]);

  const handleQuestionSelect = async (selectedQuestion) => {
    // Clear the existing timer before selecting a new question
    clearTimeout(timer);

    // Fetch the answer choices for the selected question
    try {
      const response = await axios.get(`http://127.0.0.1:5000/questions/${selectedQuestion.id}/answers`);
      setAnswerChoices(response.data.choices); // Assuming the response has a 'choices' property
      setSelectedQuestion(selectedQuestion);

      // Start the timer for 15 seconds
      setTimer(setTimeout(() => {
        // Move on to the next question after 15 seconds
        handleNextQuestion();
      }, 15000));
      
      // Reset the countdown to 15 seconds when a new question is selected
      setCountdown(15);
    } catch (error) {
      console.error('Error fetching answers:', error);
    }
  };

  const handleNextQuestion = () => {
    // Clear the timer before moving on to the next question
    clearTimeout(timer);

    // Fetch the next question from the list
    const nextIndex = questions.findIndex(q => q.id === selectedQuestion.id) + 1;
    if (nextIndex < questions.length) {
      handleQuestionSelect(questions[nextIndex]);
    } else {
      // Handle the end of the game, e.g., show a summary or redirect to another page
      console.log('End of the game');
    }
  };

  const handleAnswer = () => {
    // Add logic to send user's answer to the server if needed

    // For simplicity, let's assume a successful request and move on to the next question
    setUserAnswer('');
    handleNextQuestion();
  };

  return (
    <div>
      <h1>Trivia Game</h1>
      <div>
        <h2>Questions</h2>
        <ul>
          {questions.map((q) => (
            <li key={q.id} onClick={() => handleQuestionSelect(q)}>
              {q.question}
            </li>
          ))}
        </ul>
      </div>
      {selectedQuestion && (
        <div>
          <h2>Selected Question</h2>
          <p>{selectedQuestion.question}</p>
          <div className="countdown">{countdown}s</div>
          <form>
            {answerChoices.map((choice, index) => (
              <label key={index}>
                <input
                  type="radio"
                  value={choice}
                  checked={userAnswer === choice}
                  onChange={() => setUserAnswer(choice)}
                />
                {choice}
              </label>
            ))}
          </form>
          <button onClick={handleAnswer}>Submit Answer</button>
        </div>
      )}
    </div>
  );
};

export default Trivia;
