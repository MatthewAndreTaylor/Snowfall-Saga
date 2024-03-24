const socket = new WebSocket("ws://localhost:10000/room_events");

const roomContainer = document.querySelector(".room-container");
const createRoomButton = document.querySelector("#create-room");
const popup = document.querySelector(".popup");

socket.addEventListener("open", (event) => {
  socket.send(JSON.stringify({ type: "load", user: username }));
});

socket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "rooms":
      if (data.rooms) {
        data.rooms.forEach((room) => {
          createRoom(room.name);
          room.users.forEach((user) => {
            joinRoom(room.name, user);
          });
        });
      }
      break;

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
        socket.send(
          JSON.stringify({ type: "join", room: data.room, user: username }),
        );
      }
      break;

    case "join":
      if (data.error) {
        alert(data.error);
      } else if (data.other) {
        joinRoom(data.room, data.other);
      } else {
        joinRoom(data.room, username);
      }
      break;

    case "leave":
      if (data.error) {
        alert(data.error);
      } else if (data.other) {
        leaveRoom(data.room, data.other);
      } else {
        leaveRoom(data.room, username);
      }
      break;

    case "delete":
      deleteRoom(data.room);
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
    socket.send(
      JSON.stringify({ type: "create", room: roomName, user: username }),
    );
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
  joinButton.classList.add("join");
  joinButton.textContent = "Join Room";

  joinButton.addEventListener("click", () => {
    socket.send(
      JSON.stringify({ type: "join", room: roomName, user: username }),
    );
  });
  roomElement.appendChild(joinButton);

  const leaveButton = document.createElement("button");
  leaveButton.classList.add("leave");
  leaveButton.textContent = "Leave Room";
  leaveButton.disabled = true;
  leaveButton.classList.add("disabled");

  leaveButton.addEventListener("click", () => {
    socket.send(
      JSON.stringify({ type: "leave", room: roomName, user: username }),
    );
  });
  roomElement.appendChild(leaveButton);

  roomContainer.appendChild(roomElement);
};

const joinRoom = (room, user) => {
  const roomElement = roomContainer.querySelector(`[data-room="${room}"]`);
  if (roomElement) {
    const userList = roomElement.querySelector(".user-list");
    const userElement = document.createElement("li");
    userElement.textContent = user;
    userElement.setAttribute("data-user", user);
    userList.appendChild(userElement);

    if (user == username) {
      createRoomButton.disabled = true;
      createRoomButton.classList.add("disabled");

      const joinButton = roomElement.querySelector("button.join");
      joinButton.disabled = true;
      joinButton.classList.add("disabled");

      const leaveButton = roomElement.querySelector("button.leave");
      leaveButton.disabled = false;
      leaveButton.classList.remove("disabled");
    }
  }
};

const leaveRoom = (room, user) => {
  const roomElement = roomContainer.querySelector(`[data-room="${room}"]`);
  if (roomElement) {
    const userList = roomElement.querySelector(".user-list");
    const userElement = userList.querySelector(`[data-user="${user}"]`);
    if (userElement) {
      userList.removeChild(userElement);
    }

    if (user == username) {
      createRoomButton.disabled = false;
      createRoomButton.classList.remove("disabled");

      const joinButton = roomElement.querySelector("button.join");
      joinButton.disabled = false;
      joinButton.classList.remove("disabled");

      const leaveButton = roomElement.querySelector("button.leave");
      leaveButton.disabled = true;
      leaveButton.classList.add("disabled");
    }
  }
};

const deleteRoom = (room) => {
  const roomElement = roomContainer.querySelector(`[data-room="${room}"]`);
  if (roomElement) {
    roomContainer.removeChild(roomElement);
  }
};

createRoomButton.addEventListener("click", openPopup);
popup.addEventListener("click", closePopupOutside);
