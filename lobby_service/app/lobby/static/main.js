import { playCollisionSound } from "/static/soundModule.js";

let players = {};
let playerElements = {};
const gameContainer = document.querySelector(".game-container");
const inventoryButton = document.getElementById("inv-btn");
const sprites = document.getElementById("sprite-container");

let snowballThrow = false;
const snowballButton = document.getElementById("toggleButton");
snowballButton.addEventListener("click", () => {
  snowballButton.classList.toggle("active");
  snowballThrow = !snowballThrow;
});

// Setup a new socket connection
const socket = new WebSocket(`ws://${location.host}/echo`);

function handleMove(newX, newY) {
  const player = players[playerId];
  player.direction =
    newX > player.x ? "right" : newX < player.x ? "left" : player.direction;
  player.x = newX;
  player.y = newY;
  socket.send(JSON.stringify({ type: "playerUpdate", value: player }));
}

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "throwSnowball":
      let snowballStartX = players[data.value.id].x * 3;
      let snowballStartY = (players[data.value.id].y - 8) * 3;
      const snowball = document.createElement("div");
      snowball.classList.add("snowball");
      snowball.style.transform = `translate3d(${snowballStartX}px, ${snowballStartY}px, 0)`;

      playerElements[data.value.id].classList.add("throw");
      gameContainer.appendChild(snowball);
      setTimeout(() => {
        snowball.style.transform = `translate3d(${data.value.destinationX}px, ${data.value.destinationY}px, 0)`;
        playCollisionSound();
        setTimeout(() => {
          snowball.classList.add("explode");
          playerElements[data.value.id].classList.remove("throw");
          snowball.addEventListener(
            "transitionend",
            () => gameContainer.removeChild(snowball),
            { once: true },
          );
        }, 500);
      }, 30);
      break;
    case "playersUpdate":
      players = data.value || {};

      Object.keys(players).forEach((key) => {
        const playerState = players[key];
        addUserToBox(playerState.name);

        if (key in playerElements) {
          let el = playerElements[key];
          el.querySelector(".player_name").innerText = playerState.name;
          el.querySelector(".player_sprite").style = `background-position-y: ${
            playerState.sprite * -28
          }px`;
          el.setAttribute("data-direction", playerState.direction);
          el.style.transform = `translate3d(${playerState.x}px, ${playerState.y}px, 0)`;
        } else {
          const playerElement = document.createElement("div");
          playerElement.classList.add("player", "grid-cell");
          playerElement.innerHTML = `
                    <div class="player_shadow grid-cell"></div>
                    <div class="player_sprite grid-cell" style="background-position-y: ${
                      playerState.sprite * -28
                    }px"></div>
                    <div class="player_name-container">
                        <span class="player_name">${playerState.name}</span>
                    </div>
                    <div class="player_message-container"></div>
                    <div class="player_you-arrow"></div>`;
          playerElements[key] = playerElement;
          playerElement.setAttribute("data-direction", playerState.direction);
          playerElement.style.transform = `translate3d(${playerState.x}px, ${playerState.y}px, 0)`;
          if (key === playerId) {
            playerElement.classList.add("you");
          }
          gameContainer.appendChild(playerElement);
        }
      });
      break;
    case "playerRemoved":
      const key = data.id;
      removeUserFromBox(players[key].name);
      gameContainer.removeChild(playerElements[key]);
      delete playerElements[key];
      break;
    case "getSprites":
      const spriteMapBits = data["inventory"].toString(2).split("").reverse();
      const spriteElements = spriteMapBits
        .map((bool, index) =>
          bool === "1"
            ? `<div class="grid-item"><div class="sprite sprite-cell" data-value="${index}" style="background-position-y: ${
                index * -28
              }px;"></div></div>`
            : "",
        )
        .join("");
      sprites.innerHTML = spriteElements;
      break;
  }
});

socket.addEventListener("open", (event) => {
  console.log("WebSocket connection opened:", event);
  const message = {
    type: "playerUpdate",
    value: {
      direction: "right",
      x: 100 * Math.random() + 100,
      y: 100 * Math.random() + 100,
    },
  };
  socket.send(JSON.stringify(message));
});

socket.addEventListener("close", (event) => {
  console.log("WebSocket connection closed:", event);
  const message = {
    type: "playerRemoved",
    id: playerId,
  };
  socket.send(JSON.stringify(message));
});

// Open and close the inventory of a player's sprites
inventoryButton.addEventListener("click", () => {
  sprites.classList.toggle("hidden");
  socket.send(JSON.stringify({ type: "getSprites" }));
});

// Check if sprite costume has been clicked on using event delegation
sprites.addEventListener("click", (e) => {
  const target = e.target;
  if (target.classList.contains("sprite")) {
    const newSprite = parseInt(target.getAttribute("data-value"));
    // Send to socket only if user changes their sprite
    if (newSprite != players[playerId].sprite) {
      players[playerId].sprite = newSprite;
      const message = {
        type: "playerUpdate",
        value: players[playerId],
      };
      socket.send(JSON.stringify(message));
    }
  }
});

const chatBox = document.querySelector("#chat-box");
const messageInput = document.querySelector("#chat-input");
document
  .getElementById("message-btn")
  .addEventListener("click", () => chatBox.classList.toggle("hidden"));

const messagesSocket = new WebSocket(`ws://${location.host}/message`);

// Send a user's message
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.value.length > 0) {
    const words = e.target.value.split(" ");
    const match = words[0].match(/^@(\w+)/);
    const message = {
      type: "newMessage",
      text: e.target.value,
    };

    if (match) {
      message.type = "directMessage";
      message.to = match[1];
    }
    e.target.value = "";
    messagesSocket.send(JSON.stringify(message));
  }
});

// Receive a message from the server
messagesSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  const node = document.createElement("div");
  if (data.type != "newMessage") {
    node.style.backgroundColor = "orchid";
  }

  const messageTextNode = document.createElement("p");
  messageTextNode.appendChild(
    document.createTextNode(`${data.name}: ${data.text}`),
  );
  messageTextNode.classList.add("message-text");
  node.appendChild(messageTextNode);

  const timeNode = document.createElement("small");
  timeNode.appendChild(
    document.createTextNode(`${new Date(data.time).toLocaleString()}`),
  );
  timeNode.classList.add("message-time");
  node.appendChild(timeNode);
  node.classList.add("message");

  chatBox.appendChild(node);
  chatBox.scrollTop = chatBox.scrollHeight;
  setTimeout(() => {
    chatBox.removeChild(node);
  }, 10000);

  const playerWhoSent = playerElements[data.id];
  if (playerWhoSent) {
    const messageContainer = playerWhoSent.querySelector(
      ".player_message-container",
    );

    // Check if there are already 3 more messages in the container
    const messages = messageContainer.querySelectorAll(".player_message");
    if (messages.length >= 3) {
      messages[0].classList.add("fade-out-fast");
      messages[0].addEventListener(
        "transitionend",
        () => {
          if (messages[0] && messages[0].parentNode === messageContainer) {
            messageContainer.removeChild(messages[0]);
          }
        },
        { once: true },
      );
    }

    const bubbleNode = document.createElement("span");
    if (data.type != "newMessage") {
      bubbleNode.style.backgroundColor = "orchid";
    }

    bubbleNode.appendChild(document.createTextNode(data.text));
    bubbleNode.classList.add("player_message");
    messageContainer.appendChild(bubbleNode);
    setTimeout(() => {
      bubbleNode.classList.add("fade-out");
      bubbleNode.addEventListener(
        "transitionend",
        () => {
          if (bubbleNode && bubbleNode.parentNode === messageContainer) {
            messageContainer.removeChild(bubbleNode);
          }
        },
        { once: true },
      );
    }, 5000);
  }
});

// When a user clicks within the game container, it moves their player
gameContainer.addEventListener("click", (event) => {
  if (snowballThrow) {
    const direction =
      event.clientX > players[playerId].x * 3 ? "right" : "left";
    const messageDir = {
      type: "playerUpdate",
      value: { direction },
    };
    socket.send(JSON.stringify(messageDir));

    const message = {
      type: "throwSnowball",
      value: {
        id: playerId,
        destinationX: event.clientX,
        destinationY: event.clientY,
      },
    };
    socket.send(JSON.stringify(message));
  } else {
    const clickedElement = event.target.closest(".player");
    if (clickedElement) {
      const playerName = clickedElement.querySelector(".player_name").innerText;
      const match = messageInput.value.match(/^@(\w+)/);
      if (!match) {
        messageInput.value = `@${playerName} ${messageInput.value}`;
      } else {
        // Replace the current playerName in the message input with the new one
        messageInput.value = messageInput.value.replace(
          /^@(\w+)/,
          `@${playerName}`,
        );
      }
    } else {
      const clickX = (event.clientX - 16) / 3;
      const clickY = (event.clientY - 16) / 3;
      handleMove(clickX, clickY);
    }
  }
});

// Friend Requests
function switchTab(tabName) {
  document
    .querySelectorAll(".content, .tab")
    .forEach((element) => element.classList.remove("active"));
  document.getElementById(`${tabName}-tab`).classList.add("active");
  document.getElementById(`${tabName}-box`).classList.add("active");
}

document.getElementById("user-tab").onclick = () => switchTab("user");
document.getElementById("friend-tab").onclick = () => switchTab("friend");

const friendSocket = new WebSocket(`ws://${location.host}/friends`);
const addedUsers = new Set();

const userContainer = document.getElementById("user-container");
const userBox = userContainer.querySelector("#user-box");
const friendBox = userContainer.querySelector("#friend-box");
document.getElementById("user-container-collapse").onclick = () =>
  userContainer.classList.toggle("hidden");

const modal = document.getElementById("user-modal");
const modalContent = modal.querySelector(".modal-content");
const response = modalContent.querySelector(".request-info");

const friendRequestModal = document.getElementById("friend-request-modal");
const friendRequestButton = document.querySelector("#add-friend");
const friendRemoveButton = document.querySelector("#remove-friend");
const friendRequests = document.getElementById("friend-requests");

document.querySelector("#c1").onclick = () => (modal.style.display = "none");
document.querySelector("#c2").onclick = () =>
  (friendRequestModal.style.display = "none");
window.onclick = (event) => {
  if (event.target == modal || event.target == friendRequestModal) {
    event.target.style.display = "none";
  }
};

friendRequests.addEventListener("click", () => {
  friendSocket.send(JSON.stringify({ type: "getFriendRequests" }));
  friendRequestModal.style.display = "block";
});

friendSocket.addEventListener("open", () => {
  friendSocket.send(JSON.stringify({ type: "getFriends" }));
});

friendSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "friends":
      friendBox.innerHTML = "";
      data.friends.forEach((friendName) => {
        const friendDiv = document.createElement("div");
        friendDiv.textContent = friendName;
        friendDiv.classList.add("user-box-item");
        friendDiv.classList.add("friend-item");
        friendBox.appendChild(friendDiv);

        // Removing a friend
        friendDiv.addEventListener("click", () => {
          response.innerHTML = "";
          document.querySelector(".modal-username").textContent =
            "User: " + friendName;
          modal.style.display = "block";
          friendRequestButton.style.display = "none";
          friendRemoveButton.style.display = "block";
        });
      });
      break;
    case "friend_requests":
      const modalContent = friendRequestModal.querySelector(".modal-content");
      const list = modalContent.querySelector("#friend-request-list");
      list.innerHTML = "";
      const friendRequests = data.requests;
      if (friendRequests.length === 0) {
        list.innerHTML = "<div>No pending friend requests</div>";
      }

      friendRequests.forEach((requestingUser) => {
        const requestDiv = document.createElement("div");
        requestDiv.classList.add("friend-request");
        const fromUserSpan = document.createElement("span");
        fromUserSpan.textContent = `From: ${requestingUser}`;

        const acceptButton = document.createElement("button");
        acceptButton.textContent = "Accept";
        acceptButton.classList.add("accept-button");
        acceptButton.onclick = () => {
          friendSocket.send(
            JSON.stringify({
              type: "acceptFriendRequest",
              username: requestingUser,
            }),
          );
        };

        const rejectButton = document.createElement("button");
        rejectButton.textContent = "Reject";
        rejectButton.classList.add("reject-button");
        rejectButton.onclick = () => {
          friendSocket.send(
            JSON.stringify({
              type: "rejectFriendRequest",
              username: requestingUser,
            }),
          );
        };

        const buttonDiv = document.createElement("div");
        buttonDiv.appendChild(acceptButton);
        buttonDiv.appendChild(rejectButton);
        requestDiv.appendChild(fromUserSpan);
        requestDiv.appendChild(buttonDiv);
        list.appendChild(requestDiv);
      });
      break;
    case "sent_friend_request":
      response.innerHTML = "";
      const lineBreak = document.createElement("br");
      const requestSent = document.createElement("div");
      const isError = data.error;
      requestSent.textContent = isError ? data.error : data.success;
      requestSent.style.color = isError ? "red" : "green";

      friendRequestButton.disabled = true;
      response.append(lineBreak, requestSent);
      break;
    default:
      console.log("Message: ", data);
  }
});

friendRequestButton.addEventListener("click", () => {
  const username = document
    .querySelector(".modal-username")
    .textContent.split(": ")[1];
  friendSocket.send(
    JSON.stringify({
      type: "sendFriendRequest",
      username: username,
    }),
  );
});

friendRemoveButton.addEventListener("click", () => {
  const username = document
    .querySelector(".modal-username")
    .textContent.split(": ")[1];
  friendSocket.send(
    JSON.stringify({
      type: "removeFriend",
      username: username,
    }),
  );
  modal.style.display = "none";
});

function addUserToBox(username) {
  if (addedUsers.has(username) || username === players[playerId].name) {
    return;
  }
  const user = document.createElement("div");
  user.classList.add("user-box-item");
  user.textContent = username;
  user.setAttribute("username", username);
  userBox.appendChild(user);
  addedUsers.add(username);

  user.addEventListener("click", () => {
    response.innerHTML = "";
    friendRequestButton.disabled = false;
    document.querySelector(".modal-username").textContent = "User: " + username;
    modal.style.display = "block";
    friendRemoveButton.style.display = "none";
    friendRequestButton.style.display = "block";
  });
}

function removeUserFromBox(username) {
  if (addedUsers.has(username)) {
    const user = userBox.querySelector(`[username="${username}"]`);
    userBox.removeChild(user);
    addedUsers.delete(username);
  }
}
