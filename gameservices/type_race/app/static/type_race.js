let textElement = document.getElementById("text");
const text = textElement.innerHTML;
let characters = text.split("");
const accuracyElement = document.getElementById("accuracy");
const progressContainer = document.getElementById("progress-container");

const socket = new WebSocket(`ws://${location.host}/type_race/echo/${gameId}`);
const playerElements = {};

socket.addEventListener("open", () => {
  console.log("Connected to server");
});

socket.addEventListener("close", () => {
  console.log("Disconnected from server");
});

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "updates":
      const updates = data.updates || {};

      Object.keys(updates).forEach((key) => {
        if (key in playerElements) {
          let el = playerElements[key];
          el.style.backgroundColor = key === username ? "#96b4e08c" : "";
          el.querySelector(".progress-bar-correct").style.width = `${(updates[key][1] / updates[key][3]) * 90}%`;
          el.querySelector(".progress-bar-wrong").style.width = `${(updates[key][2] / updates[key][3]) * 90}%`;
          let reindeer = el.querySelector(".reindeer");
          reindeer.style.left = `${((updates[key][1] + updates[key][2]) / updates[key][3]) * 90 + 2}%`;
          reindeer.style.animationDuration = `${(40/(updates[key][0]+0.01)).toFixed(0)}s`;
          el.querySelector("strong").textContent = `${key}: wpm: ${updates[key][0]}`;

        } else {
          let el = document.createElement("div");
          el.classList.add("progress");
          let progress = document.createElement("div");
          progress.classList.add("progress-bar");
          let corr = document.createElement("div");
          corr.classList.add("progress-bar-correct");
          let wrong = document.createElement("div");
          wrong.classList.add("progress-bar-wrong");
          let reindeer = document.createElement("div");
          reindeer.classList.add("reindeer");
          let strong = document.createElement("strong");
          el.appendChild(progress);
          progress.appendChild(corr);
          progress.appendChild(wrong);
          progress.appendChild(reindeer);
          el.appendChild(strong);
          
          progressContainer.appendChild(el);
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
            characters[i] = `<span style="color: green; text-decoration: underline;">${text[i]}</span>`;
          } else {
            characters[i] = `<span style="color: red; text-decoration: underline;">${text[i]}</span>`;
          }
        }
      }
      updateAccuracy(progress.correct, progress.incorrect);
      slideText(index);
      break;

    case "gameOver":
      let gameOver = document.getElementById("game-over");
      gameOver.innerHTML = `The game is over! You placed in position <b>${data.place}</b> out of ${data.total} players. WPM: ${data.score}`;
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
