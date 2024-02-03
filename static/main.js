// Setup a new connection
const socket = new WebSocket(`ws://${location.host}/echo`);

function generateUUID() {
  let uuid = "";
  const possible = "abcdef0123456789";
  for (let i = 0; i < 18; i++) {
    uuid += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return uuid;
}

function randomChoice(arr) {
  return arr[Math.floor(arr.length * Math.random())];
}

const playerColors = ["blue", "red", "orange", "yellow", "green", "purple"];

let playerId;
let playerRef;
let players = {};
let playerElements = {};
let timeoutId;
let timeoutIds = [];
const gameContainer = document.querySelector(".game-container");
const nameInput = document.querySelector("#player-name");
const messageInput = document.querySelector("#chat-message");
const userBox = document.querySelector("#user-box");
const chatSend = document.querySelector("#chat-send");
const chatBox = document.querySelector("#chat-box");

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
      const checkUser = document.getElementById(`${data.id}`);
      if (!checkUser) {
          userBox.innerHTML += `<p id="${data.id}">${players[data.id].name}</p>`;
      } else {
          checkUser.innerText = `${players[data.id].name}`;
      }
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
                    <span class="Character_name">${ players[key].name || "guest"}</span>
                    </div>
                    <div class="Character_message-container hidden"></div>
                    <div class="Character_you-arrow"></div>`;
          playerElements[characterState.id] = characterElement;
          characterElement.setAttribute("data-color", characterState.color);
          characterElement.setAttribute(
            "data-direction",
            characterState.direction,
          );
          const left = characterState.x + "px";
          const top = characterState.y + "px";
          characterElement.style.transform = `translate3d(${left}, ${top}, 0)`;
          if (characterState.id === playerId) {
            characterElement.classList.add("you");
          }
          gameContainer.appendChild(characterElement);
        }
      });
      break;
    case "playerRemoved":
      const key = data.id;
      document.getElementById(`${key}`).remove();
      gameContainer.removeChild(playerElements[key]);
      delete playerElements[key];
      break;
    case 'newMessage':
        const node = document.createElement("p");
        node.appendChild(document.createTextNode(data.message));
        node.classList.add("message");
        chatBox.appendChild(node);
        chatBox.scrollTop = chatBox.scrollHeight;

        const playerWhoSent = playerElements[data.id];

        const messageContainer = playerWhoSent.querySelector(".Character_message-container");

        if (messageContainer.getElementsByClassName("Character_message").length === 3) {
            messageContainer.removeChild(playerWhoSent.querySelector(".Character_message"));
        }

        const bubbleNode = document.createElement("span");
        bubbleNode.appendChild(document.createTextNode(data.message));
        bubbleNode.classList.add("Character_message");
        messageContainer.appendChild(bubbleNode);

        playerWhoSent.querySelector(".Character_message-container").classList.remove("hidden");
        break
      case 'timeoutMessage':
        const timeoutElements = playerElements[data.id];
        const messageNode = timeoutElements.querySelector(".Character_message");
        const containerNode = timeoutElements.querySelector(".Character_message-container");
        containerNode.removeChild(messageNode);
        if (containerNode.getElementsByClassName("Character_message").length === 0) {
            containerNode.classList.add("hidden");
        }
        break
  }
});

socket.addEventListener("open", (event) => {
  console.log("WebSocket connection opened:", event);
  playerId = generateUUID();
  const message = {
    type: "playerUpdate",
    value: {
      id: playerId,
      name: "guest",
      direction: "right",
      color: randomChoice(playerColors),
      x: 0,
      y: 0,
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

nameInput.addEventListener("change", (e) => {
  const oldName = players[playerId].name;
  const newName = e.target.value || "guest";
  nameInput.value = newName;
  const updated_player = players[playerId];
  updated_player.name = newName;

  const message = {
    type: "playerUpdate",
    value: updated_player,
    oldname: oldName
  };
  socket.send(JSON.stringify(message));
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === 'Enter') {
      if (timeoutIds.length === 3) {
          clearTimeout(timeoutIds.at(0));
          timeoutIds = timeoutIds.slice(1);
      }
      const sender = players[playerId];

      timeoutId = setTimeout(() => {
          const message = {
              type: 'timeoutMessage',
              id: playerId
          };
          socket.send(JSON.stringify(message));
          timeoutIds = timeoutIds.slice(1);
      }, 5000);
      timeoutIds.push(timeoutId);

      const message = {
          type: 'newMessage',
          sender: sender.name,
          data: e.target.value,
          id: playerId
      };
      e.target.value = '';
      socket.send(JSON.stringify(message));
  }
});

chatSend.addEventListener("click", () => {
  if (timeoutIds.length === 3) {
    clearTimeout(timeoutIds.at(0));
    timeoutIds = timeoutIds.slice(1);
  }
  const sender = players[playerId];

  timeoutId = setTimeout(() => {
      const message = {
          type: 'timeoutMessage',
          id: playerId
      };
      socket.send(JSON.stringify(message));
      timeoutIds = timeoutIds.slice(1);
  }, 5000);
  timeoutIds.push(timeoutId);

  const message = {
      type: 'newMessage',
      sender: sender.name,
      data: e.target.value,
      id: playerId
  };
  e.target.value = '';
  socket.send(JSON.stringify(message));
});

gameContainer.addEventListener("click", (event) => {
  const clickX = (event.clientX - 16) / 3;
  const clickY = (event.clientY - 16) / 3;
  handleMove(clickX, clickY);
});
