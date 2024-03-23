const roomContainer = document.querySelector(".room-container");

const openPopup = () => {
  document.querySelector(".popup").style.display = "block";
};

const closePopup = () => {
  document.querySelector(".popup").style.display = "none";
};

const closePopupOutside = (event) => {
  if (event.target === document.querySelector(".popup")) {
    closePopup();
  }
};

const confirmRoom = () => {
  const roomName = document.querySelector("#room-name-input").value.trim();
  if (roomName !== "") {
    createRoom(roomName);
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
};

const joinRoom = (room) => {
  console.log("joining room", room);
};

document.querySelector("#create-room").addEventListener("click", openPopup);
document.querySelector(".popup").addEventListener("click", closePopupOutside);
