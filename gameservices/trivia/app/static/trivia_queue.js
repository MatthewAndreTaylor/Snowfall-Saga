const socket = io.connect(`ws://${location.host}/trivia`);

// Send the username after the socket connection is established
socket.on("connect", () => {
  socket.emit("username", username);
});

socket.addEventListener("user_list", (event) => {
  console.log("Received user list event:", event);
  displayUsersList(event);
});

socket.on("num_questions", (data) => {
  console.log("Received num_questions event:", data);
  displayNumQuestions(data);
});

socket.on("party_leader", function () {
  console.log("Received party leader event.");
  // Check if the client is the party leader
  var isLeader = confirm("Do you want to change the number of questions?");
  if (isLeader) {
    // Prompt the party leader to change num_questions or timer values
    var newNumQuestions = prompt("Enter new number of questions:");
    if (newNumQuestions !== null) {
      // If the user entered a value, send it to the server
      socket.emit("num_questions", parseInt(newNumQuestions));
    }
  }
});

function displayUsersList(userList) {
  console.log("Received user list:", userList);

  const usersList = document.getElementById("usersList");

  // Check if userList is defined before attempting to iterate
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

function displayNumQuestions(numQuestions) {
  console.log("Received num_questions:", numQuestions);

  // Display the num_questions value on the screen
  const numQuestionsElement = document.createElement("p");
  const textNode = document.createTextNode(
    `Number of Questions: ${numQuestions}`,
  );
  numQuestionsElement.appendChild(textNode);
  document.body.appendChild(numQuestionsElement);
}

function displayTimer(timerValue) {
  console.log("Received timer:", timerValue);

  // Display the timer value on the screen
  const timerElement = document.createElement("p");
  const textNode = document.createTextNode(`Timer: ${timerValue} seconds`);
  timerElement.appendChild(textNode);
  document.body.appendChild(timerElement);
}

document.getElementById("startButton").addEventListener("click", () => {
  socket.emit("start_game");
});

socket.on("switch_page", (data) => {
  sessionStorage.setItem("username", username);
  window.location.href = data.url;
});