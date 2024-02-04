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

function handleMove(newX, newY) {
  const button = document.querySelector(".christmas-tree-button");
  const buttonX = (button.getBoundingClientRect().left - 16) / 3;
  const buttonY = (button.getBoundingClientRect().top - 16) / 3;
  const buttonWidth = (button.getBoundingClientRect().width - 16) / 3;
  const buttonHeight = (button.getBoundingClientRect().height - 16) / 3;

  if (
    newX < buttonX + buttonWidth &&
    newX > buttonX &&
    newY < buttonY + buttonHeight &&
    newY > buttonY
  ) {
    newX = buttonX - 10;
    newY = buttonY + buttonHeight / 2;
  }

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
    case "playersUpdate":
      players = data.value || {};
      Object.keys(players).forEach((key) => {
        const characterState = players[key];
        if (key in playerElements) {
          let el = playerElements[key];
          el.querySelector(".Character_name").innerText = characterState.name;
          el.setAttribute("data-color", characterState.color);
          el.setAttribute("data-direction", characterState.direction);
          const left = characterState.x + "px";
          const top = characterState.y + "px";
          el.style.transform = `translate3d(${left}, ${top}, 0)`;
        } else {
          const characterElement = document.createElement("div");
          characterElement.classList.add("Character", "grid-cell");
          characterElement.innerHTML = `
                    <div class="Character_shadow grid-cell"></div>
                    <div class="Character_sprite grid-cell"></div>
                    <div class="Character_name-container">
                        <span class="Character_name">${characterState.name}</span>
                    </div>
                    <div class="Character_message-container"></div>
                    <div class="Character_you-arrow"></div>`;
          playerElements[key] = characterElement;
          characterElement.setAttribute("data-color", characterState.color);
          characterElement.setAttribute(
            "data-direction",
            characterState.direction,
          );
          const left = characterState.x + "px";
          const top = characterState.y + "px";
          characterElement.style.transform = `translate3d(${left}, ${top}, 0)`;
          if (key === playerId) {
            characterElement.classList.add("you");
          }
          gameContainer.appendChild(characterElement);
        }
      });
      break;
    case "playerRemoved":
      const key = data.id;
      gameContainer.removeChild(playerElements[key]);
      delete playerElements[key];
      break;
    case 'newMessage':
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
        const messageContainer = playerWhoSent.querySelector(".Character_message-container");

        // Check if there are already 3 more messages in the container  
        const messages = messageContainer.querySelectorAll(".Character_message");
        if (messages.length >= 3) {
          messages[0].classList.add("fade-out");
          messages[0].addEventListener("transitionend", () => {
            messageContainer.removeChild(messages[0]);
          }, { once: true });
        }

        const bubbleNode = document.createElement("span");
        bubbleNode.appendChild(document.createTextNode(data.text));
        bubbleNode.classList.add("Character_message");
        messageContainer.appendChild(bubbleNode);
        setTimeout(() => {
          bubbleNode.classList.add("fade-out");
          bubbleNode.addEventListener("transitionend", () => {
            messageContainer.removeChild(bubbleNode);
          }, { once: true });
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
      x: 100* Math.random() + 100,
      y: 100* Math.random() + 100,
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
  if (e.key === 'Enter' && e.target.value.length > 0) {
      const message = {
          type: 'newMessage',
          text: e.target.value,
      };
      e.target.value = '';
      socket.send(JSON.stringify(message));
  }
});

// When a user clicks within the game container it moves their player
gameContainer.addEventListener("click", (event) => {
  const clickX = (event.clientX - 16) / 3;
  const clickY = (event.clientY - 16) / 3;
  handleMove(clickX, clickY);
});
