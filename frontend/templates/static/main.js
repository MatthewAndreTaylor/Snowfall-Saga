// Setup a new connection
const socket = new WebSocket(`ws://${location.host}/echo`);

function generateUUID() {
    let uuid = "";
    const possible = "abcdef0123456789";
    for (let i = 0; i < 32; i++) {
        uuid += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return uuid;
}

function randomChoice(arr) {
    return arr[Math.floor(arr.length * Math.random())];
}

const playerColors = ["blue", "red", "orange", "yellow", "green", "purple"];

let playerId;
let timeoutId;
let playerRef;
let players = {};
let playerElements = {};
let timeoutIds = [];
const gameContainer = document.querySelector(".game-container");
const nameInput = document.querySelector("#player-name");
const messageInput = document.querySelector("#chat-message");
const userBox = document.querySelector("#user-box");
const chatSend = document.querySelector("#chat-send");
const chatBox = document.querySelector("#chat-box");

function handleArrowPress(deltaX, deltaY) {
    players[playerId].x = players[playerId].x + deltaX;
    players[playerId].y = players[playerId].y + deltaY;
    if (deltaX === 1) {
        players[playerId].direction = "right";
    }
    else if (deltaX === -1) {
      players[playerId].direction = "left";
    }
    const message = {
        type: 'playerMove',
        value: players[playerId],
        id: playerId
    };
    socket.send(JSON.stringify(message));
}

socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    console.log(data);

    switch (data.type) {
        case 'playersUpdate':
            players = data.value || {}
            const checkUser = document.getElementById(`${data.id}`);
            if (!checkUser) {
                userBox.innerHTML += `<p id="${data.id}">${players[data.id].name}</p>`;
            } else {
                checkUser.remove();
                userBox.innerHTML += `<p id="${data.id}">${players[data.id].name}</p>`;
            }
            Object.keys(players).forEach((key) => {
                const characterState = players[key];
                if (!(key in playerElements)) {
                    const characterElement = document.createElement("div");
                    characterElement.classList.add("Character", "grid-cell");
                    characterElement.innerHTML = `
                    <div class="Character_shadow grid-cell"></div>
                    <div class="Character_sprite grid-cell"></div>
                    <div class="Character_name-container">
                        <span class="Character_name">${ players[key].name || "guest"}</span>
                    </div>
                    <div class="Character_message-container hidden">
                    </div>
                    <div class="Character_you-arrow"></div>`;
                    playerElements[characterState.id] = characterElement;
                    characterElement.setAttribute("data-color", characterState.color);
                    characterElement.setAttribute("data-direction", characterState.direction);
                    const left = 16 * characterState.x + "px";
                    const top = 16 * characterState.y + "px";
                    characterElement.style.transform = `translate3d(${left}, ${top}, 0)`;
                    if (characterState.id === playerId) {
                      characterElement.classList.add("you");
                    }
                    gameContainer.appendChild(characterElement);
                } else {
                    let el = playerElements[key];
                    el.querySelector(".Character_name").innerText = characterState.name;
                }
            });
            break
        case 'playerRemoved':
            const key = data.id;
            const removeUser = document.getElementById(`${key}`);
            removeUser.remove();
            gameContainer.removeChild(playerElements[key]);
            delete playerElements[key];
            break
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
        case 'playersMove':
            players = data.value || {}
            console.log(data.id)
            const moveState = players[data.id];
            console.log(moveState);
            let el = playerElements[data.id];
            el.setAttribute("data-color", moveState.color);
            el.setAttribute("data-direction", moveState.direction);
            const left = 16 * moveState.x + "px";
            const top = 16 * moveState.y + "px";
            el.style.transform = `translate3d(${left}, ${top}, 0)`;
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
      type: 'playerUpdate',
      value: {
        id: playerId,
        name: 'guest',
        direction: "right",
        color: randomChoice(playerColors),
        x: 0,
        y: 0
      }
    };
    socket.send(JSON.stringify(message));
});

socket.addEventListener("close", (event) => {
    console.log("WebSocket connection closed:", event);
    const message = {
      type: 'playerRemoved',
      id: playerId,
      name: players[playerId].name
    };
    socket.send(JSON.stringify(message));
});

nameInput.addEventListener("change", (e) => {
    const oldName = players[playerId].name;
    const newName = e.target.value || "guest";
    nameInput.value = newName;
    const updated_player = players[playerId];
    updated_player.name = newName

    const message = {
        type: 'playerUpdate',
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
        console.log("Entered keydown event");
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
})

chatSend.addEventListener("click", () => {
    const sender = players[playerId];

    const message = {
        type: 'newMessage',
        sender: sender.name,
        data: messageInput.value
    };
    messageInput.value = '';
    socket.send(JSON.stringify(message));
})

new KeyPressListener("ArrowLeft", () => handleArrowPress(-1, 0));
//new KeyPressListener("KeyA", () => handleArrowPress(-1, 0));
new KeyPressListener("ArrowUp", () => handleArrowPress(0, -1));
//new KeyPressListener("KeyW", () => handleArrowPress(0, -1));
new KeyPressListener("ArrowRight", () => handleArrowPress(1, 0));
//new KeyPressListener("KeyD", () => handleArrowPress(1, 0));
new KeyPressListener("ArrowDown", () => handleArrowPress(0, 1));
//new KeyPressListener("KeyS", () => handleArrowPress(0, 1));