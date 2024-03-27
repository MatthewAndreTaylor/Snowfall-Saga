let textElement = document.getElementById("text");
const text = textElement.innerHTML;
let characters = text.split("");
const accuracyElement = document.getElementById("accuracy");

const socket = new WebSocket(`ws://${location.host}/type_race/echo/${gameId}`);

const playerElements = {};

socket.addEventListener("open", () => {
  console.log("Connected to server");
});

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "updates":
      const updates = data.updates || {};

      Object.keys(updates).forEach((key) => {
        if (key in playerElements) {
          let el = playerElements[key];
          el.textContent =
            key +
            ": wpm: " +
            updates[key][0] +
            ", characters typed: " +
            updates[key][1];
        } else {
          let el = document.createElement("div");
          if (key === username) {
            el.classList.add("you");
          }
          el.textContent =
            key +
            ": wpm: " +
            updates[key][0] +
            ", characters typed: " +
            updates[key][1];
          document.body.appendChild(el);
          playerElements[key] = el;
        }
      });
      break;
  }
});

function updateAccuracy(correct, incorrect) {
  const accuracy =
    correct + incorrect > 0 ? (correct / (correct + incorrect)) * 100 : 0;
  accuracyElement.textContent = `Accuracy: ${accuracy.toFixed(2)}%`;
}

const inputSocket = new WebSocket(
  `ws://${location.host}/type_race/input/${gameId}`,
);

window.addEventListener("keydown", (event) => {
  event.preventDefault();
  console.log(event.key);

  if (/^[a-zA-Z\s,.!?'":;]$/.test(event.key) || event.key == "Backspace") {
    inputSocket.send(JSON.stringify({ key: event.key }));
  } else {
    console.log("Invalid key");
  }
});

inputSocket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "progress":
      const progress = data.progress || {};
      let index = progress.typed.length - 1;

      for (let i = 0; i < text.length; i++) {
        if (i > index) {
          characters[i] = text[i];
        } else {
          if (progress.typed[i] === text[i]) {
            characters[i] = `<span style="color: green">${text[i]}</span>`;
          } else {
            characters[i] = `<span style="color: red">${text[i]}</span>`;
          }
        }
      }
      updateAccuracy(progress.correct, progress.incorrect);
      slideText(index);

      console.log(progress);
      break;

    case "gameOver":
      let gameOver = document.getElementById("game-over");
      gameOver.innerHTML = "The game is over!";
      break;
  }
});

function slideText(index) {
  let slice = characters.slice(
    Math.max(0, index - 10),
    Math.min(characters.length, index + 105),
  );
  textElement.innerHTML = slice.join("");
}
