// Setup a new socket connection
const socket = new WebSocket(`ws://${location.host}/echo`);

const collisionSound = new Audio("/static/audio/snowballHit.mp3");

function playCollisionSound() {
  collisionSound.play();
}

function randomChoice(arr) {
  return arr[Math.floor(arr.length * Math.random())];
}

const playerColors = ["blue", "red", "orange", "yellow", "green", "purple"];

let playerRef;
let players = {};
let playerElements = {};
const gameContainer = document.querySelector(".game-container");

const userBox = document.querySelector("#user-box");
const chatBox = document.querySelector("#chat-box");
const messageInput = document.querySelector("#chat-input");

function handleMove(newX, newY) {
  if (newX > players[playerId].x) {
    players[playerId].direction = "right";
  } else if (newX < players[playerId].x) {
    players[playerId].direction = "left";
  }
  players[playerId].x = newX;
  players[playerId].y = newY;
  const message = {
    type: "playerUpdate",
    value: players[playerId],
  };
  socket.send(JSON.stringify(message));
}

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "throwSnowball":
      const snowballStartX = players[data.value.id].x * 3;
      const snowballStartY = (players[data.value.id].y - 8) * 3;
      const targetX = data.value.destinationX;
      const targetY = data.value.destinationY;

      const deltaX = targetX - snowballStartX;
      const deltaY = targetY - snowballStartY;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      const speed = 9; // Adjust speed as needed
      const velocityX = (deltaX / distance) * speed;
      const velocityY = (deltaY / distance) * speed;

      const snowball = document.createElement("div");
      snowball.classList.add("snowball");
      snowball.style.left = snowballStartX + "px";
      snowball.style.top = snowballStartY + "px";
      document.body.appendChild(snowball);

      snowball.classList.add("throw-animation");

      const animationInterval = setInterval(() => {
        const snowballX = parseInt(snowball.style.left);
        const snowballY = parseInt(snowball.style.top);
        if (
          Math.abs(snowballX - snowballStartX) >= Math.abs(deltaX) ||
          Math.abs(snowballY - snowballStartY) >= Math.abs(deltaY)
        ) {
          clearInterval(animationInterval);
          snowball.remove();
          playCollisionSound();
          snowball.classList.add("collision");
          const explosion = document.createElement("div");
          explosion.classList.add("explosion");
          explosion.style.left = snowballX + "px";
          explosion.style.top = snowballY + "px";
          document.body.appendChild(explosion);
        }
        snowball.style.left = parseInt(snowball.style.left) + velocityX + "px";
        snowball.style.top = parseInt(snowball.style.top) + velocityY + "px";
      }, 10);
      break;

    case "playersUpdate":
      players = data.value || {};
      Object.keys(players).forEach((key) => {
        const playerState = players[key];
        if (key in playerElements) {
          let el = playerElements[key];
          el.querySelector(".player_name").innerText = playerState.name;
          el.setAttribute("data-color", playerState.color);
          el.setAttribute("data-direction", playerState.direction);
          const left = playerState.x + "px";
          const top = playerState.y + "px";
          el.style.transform = `translate3d(${left}, ${top}, 0)`;
        } else {
          const playerElement = document.createElement("div");
          playerElement.classList.add("player", "grid-cell");
          playerElement.innerHTML = `
                    <div class="player_sprite grid-cell"></div>
                    <div class="player_name-container">
                        <span class="player_name">${playerState.name}</span>
                    </div>
                    <div class="player_message-container"></div>
                    <div class="player_you-arrow"></div>
                    <div class="player_shadow grid-cell"></div>`;
          playerElements[key] = playerElement;
          playerElement.setAttribute("data-color", playerState.color);
          playerElement.setAttribute("data-direction", playerState.direction);
          const left = playerState.x + "px";
          const top = playerState.y + "px";
          playerElement.style.transform = `translate3d(${left}, ${top}, 0)`;
          if (key === playerId) {
            playerElement.classList.add("you");
          }
          gameContainer.appendChild(playerElement);
        }
      });
      break;
    case "playerRemoved":
      const key = data.id;
      gameContainer.removeChild(playerElements[key]);
      delete playerElements[key];
      break;
    case "newMessage":
      const node = document.createElement("p");
      node.appendChild(document.createTextNode(`${data.name}: ${data.text}`));
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

        const messages = messageContainer.querySelectorAll(".player_message");
        if (messages.length >= 3) {
          messages[0].classList.add("fade-out");
          messages[0].addEventListener(
            "transitionend",
            () => {
              messageContainer.removeChild(messages[0]);
            },
            { once: true },
          );
        }

        const bubbleNode = document.createElement("span");
        bubbleNode.appendChild(document.createTextNode(data.text));
        bubbleNode.classList.add("player_message");
        messageContainer.appendChild(bubbleNode);
        setTimeout(() => {
          bubbleNode.classList.add("fade-out");
          bubbleNode.addEventListener(
            "transitionend",
            () => {
              messageContainer.removeChild(bubbleNode);
            },
            { once: true },
          );
        }, 5000);
      }
      break;
  }
});

socket.addEventListener("open", (event) => {
  console.log("WebSocket connection opened:", event);
  const message = {
    type: "playerUpdate",
    value: {
      direction: "right",
      color: randomChoice(playerColors),
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

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.value.length > 0) {
    const message = {
      type: "newMessage",
      text: e.target.value,
    };
    e.target.value = "";
    socket.send(JSON.stringify(message));
  }
});

gameContainer.addEventListener("click", (event) => {
  const clickX = (event.clientX - 16) / 3;
  const clickY = (event.clientY - 16) / 3;
  handleMove(clickX, clickY);
});

// Handle user choice - Snowball
gameContainer.addEventListener("contextmenu", (event) => {
  event.preventDefault();

  const message = {
    type: "throwSnowball",
    value: {
      id: playerId,
      destinationX: event.clientX,
      destinationY: event.clientY,
    },
  };
  socket.send(JSON.stringify(message));
});
