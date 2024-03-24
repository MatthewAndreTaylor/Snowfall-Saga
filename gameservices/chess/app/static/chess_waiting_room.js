const socket = new WebSocket(`ws://${document.domain}:${location.port}/chess`);

socket.addEventListener("open", (event) => {
  socket.send(JSON.stringify({ type: "username", username: username }));
});

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "playerList":
      displayUsersList(data["data"]);
      break;

    case "switchPage":
      sessionStorage.setItem("username", username);
      sessionStorage.setItem("gameId", gameId);
      window.location.href = data.url + "/" + gameId;
      break;
  }
});

function displayUsersList(userList) {
  console.log("Received user list:", userList);

  const usersList = document.getElementById("player-list");

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

document.getElementById("startButton").addEventListener("click", () => {
  socket.send(JSON.stringify({ type: "startGame" }));
});
