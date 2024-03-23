const createRoomSocket = new WebSocket("ws://localhost:10000/create_room");

const roomContainer = document.querySelector(".room-container");
const popup = document.querySelector(".popup");

createRoomSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "create":
      createRoom(data.room);
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
    createRoomSocket.send(JSON.stringify({ room: roomName }));
    closePopup();
  } else {
    alert("Please enter a room name");
  }
};

const createRoom = (roomName) => {
  const roomElement = document.createElement("div");
  roomElement.classList.add("room");

  const roomTitle = document.createElement("h2");
  roomTitle.textContent = roomName;
  roomElement.appendChild(roomTitle);

  const joinButton = document.createElement("button");
  joinButton.textContent = "Join Room";
  joinButton.addEventListener("click", () => joinRoom(roomName));
  roomElement.appendChild(joinButton);

  roomContainer.appendChild(roomElement);
  joinRoom(roomName);
};

const joinRoom = (room) => {
  console.log("joining room", room);
};

document.querySelector("#create-room").addEventListener("click", openPopup);
popup.addEventListener("click", closePopupOutside);
