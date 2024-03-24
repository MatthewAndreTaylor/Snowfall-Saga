const loadRoomSocket = new WebSocket("ws://localhost:10000/load_rooms");
const createRoomSocket = new WebSocket("ws://localhost:10000/create_room");
const joinRoomSocket = new WebSocket("ws://localhost:10000/join_room");

const roomContainer = document.querySelector(".room-container");
const popup = document.querySelector(".popup");
const createRoomButton = document.querySelector("#create-room");

loadRoomSocket.addEventListener("open", (event) => {
  loadRoomSocket.send(JSON.stringify({ type: "load", user: username }));
});

loadRoomSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "rooms":
      if (data.rooms) {
        data.rooms.forEach((room) => {
          createRoom(room);
        });
      }
      break;
  }
});

createRoomSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "create":
      if (data.error) {
        alert(data.error);
      } else if (data.other) {
        createRoom(data.room);
      } else {
        closePopup();
        createRoom(data.room);

        createRoomButton.disabled = true;
        createRoomButton.classList.add("disabled");
        joinRoomSocket.send(
          JSON.stringify({ room: data.room, user: username }),
        );
      }
      break;
  }
});

joinRoomSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "join":
      if (data.error) {
        alert(data.error);
      } else if (data.other) {
        joinRoom(data.room, data.other);
      } else {
        joinRoom(data.room, username);
      }
      break;
  }
});

const openPopup = () => {
  popup.style.display = "block";
};

const closePopup = () => {
  const input = document.querySelector("#room-name-input");
  input.value = "";
  popup.style.display = "none";
};

const closePopupOutside = (event) => {
  if (event.target === popup) {
    closePopup();
  }
};

const confirmRoom = () => {
  const roomName = document.querySelector("#room-name-input").value.trim();
  if (roomName !== "") {
    createRoomSocket.send(JSON.stringify({ room: roomName, user: username }));
  } else {
    alert("Please enter a room name");
  }
};

const createRoom = (roomName) => {
  const roomElement = document.createElement("div");
  roomElement.classList.add("room");
  roomElement.setAttribute("data-room", roomName);

  const roomTitle = document.createElement("h2");
  roomTitle.textContent = roomName;
  roomElement.appendChild(roomTitle);

  const userList = document.createElement("ul");
  userList.classList.add("user-list");
  roomElement.appendChild(userList);

  const joinButton = document.createElement("button");
  joinButton.textContent = "Join Room";

  joinButton.addEventListener("click", () => {
    joinRoomSocket.send(JSON.stringify({ room: roomName, user: username }));
  });
  roomElement.appendChild(joinButton);

  roomContainer.appendChild(roomElement);
};

const joinRoom = (room, username) => {
  const roomElement = roomContainer.querySelector(`[data-room="${room}"]`);
  if (roomElement) {
    const userList = roomElement.querySelector(".user-list");
    const userElement = document.createElement("li");
    userElement.textContent = username;
    userList.appendChild(userElement);
  }
};

createRoomButton.addEventListener("click", openPopup);
popup.addEventListener("click", closePopupOutside);
