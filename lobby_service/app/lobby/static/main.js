// Setup a new socket connection
const socket = new WebSocket(`ws://${location.host}/echo`);

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

const inventoryContainer = document.querySelector(".inventory-container");
const inventoryButton = document.querySelector("#inv-btn");
const spriteGrid = document.querySelector("#sprite-grid");

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
  //console.log(data);

  switch (data.type) {
    case "playersUpdate":
      players = data.value || {};
      Object.keys(players).forEach((key) => {
        const playerState = players[key];
        if (key in playerElements) {
          let el = playerElements[key];
          el.querySelector(".player_name").innerText = playerState.name;
          el.querySelector(".player_sprite").style = `background-position-y: ${
            playerState.sprite * -28
          }px`;
          el.setAttribute("data-direction", playerState.direction);
          const left = playerState.x + "px";
          const top = playerState.y + "px";
          el.style.transform = `translate3d(${left}, ${top}, 0)`;
        } else {
          const playerElement = document.createElement("div");
          playerElement.classList.add("player", "grid-cell");
          playerElement.innerHTML = `
                    <div class="player_sprite grid-cell" style="background-position-y: ${
                      playerState.sprite * -28
                    }px"></div>
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

        // Check if there are already 3 more messages in the container
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
    case "getSprites":
      const binary = data["inventory"].toString(2);
      const binaryArr = binary.split("").reverse();

      const sprites = document.querySelector("#sprite-container");

      binaryArr.forEach((bool, index) => {
        if (bool === "1") {
          sprites.innerHTML += `
          <div class="grid-item">
            <div class="sprite sprite-cell" data-value="${index}" style="background-position-y: ${
              index * -28
            }px;"></div>
          </div>`;
        }
      });
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

// Send a user's message by pressing 'Enter'
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

// Open and close the inventory of a player's sprites
inventoryButton.addEventListener("click", () => {
  let sprites = document.querySelector("#sprite-container");

  if (sprites !== null) {
    sprites.parentNode.removeChild(sprites);
  } else {
    spriteGrid.innerHTML += `<div id="sprite-container" class="sprite-container"></div>`;
    const message = {
      type: "getSprites",
    };
    socket.send(JSON.stringify(message));
  }
});

// Check if sprite costume has been clicked on using event delegation
spriteGrid.addEventListener("click", (e) => {
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

// When a user clicks within the game container, it moves their player
gameContainer.addEventListener("click", (event) => {
  const clickX = (event.clientX - 16) / 3;
  const clickY = (event.clientY - 16) / 3;
  handleMove(clickX, clickY);
});
