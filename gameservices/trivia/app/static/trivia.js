const socket = io.connect(
  `ws://${document.domain}:${location.port}/trivia/game/${id}`,
);
let username;

socket.on("connect", () => {
  // Connection established, print a message on the screen
  document.getElementById("message").innerText =
    "Connected to WebSocket Server";
  username = sessionStorage.getItem("username") || "Guest";
  socket.emit("register", username);
});

document.addEventListener("DOMContentLoaded", function () {
  const lobbyButton = document.getElementById("lobbyButton");
  lobbyButton.addEventListener("click", function () {
    window.location.href = "http://127.0.0.1:5000/";
  });
});

socket.on("disconnect", () => {
  // Connection lost, print a message on the screen
  document.getElementById("message").innerText =
    "Disconnected from WebSocket Server";
});

socket.addEventListener("user_list", (event) => {
  console.log("Received user list event:", event);
  displayUsersList(event);
});

socket.on("question", (question) => {
  console.log("Received question" + question.question);
});

socket.on("updated_points", (updatedPoints) => {
  updateScores(updatedPoints);
});

function displayUsersList(userList) {
  console.log("Received user list:", userList);

  const usersList = document.getElementById("usersList");

  // Check if userList is defined before attempting to iterate over it
  if (userList) {
    console.log("Number of users:", userList.length);

    usersList.innerHTML = "";

    for (const user of userList) {
      console.log("Adding user:", user);
      const node = document.createElement("li");
      const textnode = document.createTextNode(user);
      node.appendChild(textnode);
      usersList.appendChild(node);
    }

    // Set display property to 'block' for the <ul> element
    usersList.style.display = "block";
  } else {
    console.log("User list is undefined or empty.");
  }
}

function displayQuestion(question) {
  // Display question
  const questionElement = document.createElement("p");
  questionElement.textContent = question["question"];
  questionElement.classList.add("question");
  // document.body.appendChild(questionElement);

  const questionContainer = document.getElementById("question-container");
  questionContainer.innerHTML = ""; // Clear previous content
  questionContainer.appendChild(questionElement);

  const optionsContainer = document.querySelector(".options-container");
  optionsContainer.innerHTML = ""; // Clear previous content

  // Display options as buttons
  for (let i = 1; i <= 4; i++) {
    const optionKey = "option" + i;
    const optionButton = document.createElement("button");
    optionButton.textContent = question[optionKey];
    optionButton.addEventListener("click", () => {
      sendAnswer(optionKey);
      // Hide the buttons after clicking
      hideButtons();
    });
    // document.body.appendChild(optionButton);
    optionsContainer.appendChild(optionButton);
  }

  function hideButtons() {
    // Select all buttons and hide them
    // const buttons = document.querySelectorAll('button');
    const buttons = document.querySelectorAll(".options-container button");
    buttons.forEach((button) => {
      button.style.display = "none";
      button.style.userSelect = "none";
    });
  }
}

function sendAnswer(selectedOption) {
  socket.emit("answer", selectedOption);
}

// Listen for 'question' event from the server
socket.on("question", (question) => {
  console.log("Received question from server:", question);
  displayQuestion(question);
});

socket.on("correct", (updatedPoints) => {
  displayFeedback("Correct", "correct");
  updateScores(updatedPoints);
});

socket.on("incorrect", (updatedPoints) => {
  displayFeedback("Incorrect", "incorrect");
  updateScores(updatedPoints);
});

function displayFeedback(message, className) {
  const feedbackContainer = document.getElementById("feedback-container");
  feedbackContainer.textContent = message;
  feedbackContainer.className = className;
}

function updateScores(points) {
  const scoresList = document.getElementById("scoresList");

  if (points) {
    scoresList.innerHTML = "";

    for (const [user, score] of Object.entries(points)) {
      const node = document.createElement("li");
      const textnode = document.createTextNode(`${user}: ${score} points`);
      node.appendChild(textnode);
      scoresList.appendChild(node);
    }
  } else {
    console.log("Points object is undefined or empty.");
  }
}
