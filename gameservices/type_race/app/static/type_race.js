let gameId = sessionStorage.getItem("gameId");

const socket = new WebSocket(
  `ws://${document.domain}:${location.port}/type_race/game/${gameId}`,
);

let textElement = document.getElementById("text");

let text = textElement.innerHTML;

const accuracyElement = document.getElementById("accuracy");

let progressList = document.getElementById("progress-list");

let i = 0;

let characters = text.split("");

let inputtedString = "";

let totalCount = 0;

let correct = 0;

let incorrect = 0;

let accuracy = 0;

let countdownValue = 3;

let done = false;

slideText();

document.addEventListener("DOMContentLoaded", function () {
  const lobbyButton = document.getElementById("lobbyButton");
  lobbyButton.addEventListener("click", function () {
    window.location.href = "http://127.0.0.1:5000/";
  });
});

socket.addEventListener("open", (event) => {
  socket.send(
    JSON.stringify({
      type: "username",
      username: sessionStorage.getItem("username"),
    }),
  );
});

function handleKey(e) {
  e.preventDefault();
  document.getElementById("countdown").innerText = "";

  console.log(e.key);

  if (inputtedString.length >= text.length) {
    return;
  }
  if (/^[a-zA-Z\s,.!?'":;]$/.test(event.key)) {
    inputtedString = inputtedString + e.key;
    console.log(inputtedString);
    console.log(text);
    if (inputtedString[i] == text[i]) {
      characters[i] =
        '<span style="color: #7fffd4;">' + characters[i] + "</span>";
      if (i == totalCount) {
        if (!done) {
          correct = correct + 1;
        }
        totalCount = totalCount + 1;
      }
    } else {
      characters[i] = '<span style="color: red;">' + characters[i] + "</span>";
      if (i == totalCount) {
        if (!done) {
          incorrect = incorrect + 1;
        }
        totalCount = totalCount + 1;
      }
    }
    updateAccuracy();
    //    textElement.innerHTML = characters.join('');
    slideText();
    i = i + 1;
  } else if (event.key == "Backspace") {
    i = i - 1;
    characters[i] = characters[i].split(">")[1][0];
    //    textElement.innerHTML = characters.join('');
    slideText();
    inputtedString = inputtedString.slice(0, -1);
  }

  if (correct >= 200 && !done) {
    socket.send(JSON.stringify({ type: "win" }));
    done = true;
  }

  if (inputtedString.length >= text.length) {
    socket.send(JSON.stringify({ type: "done" }));
  }
}

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "playerUpdate":
      progressList.innerHTML = "";

      for (let username in data) {
        if (data.hasOwnProperty(username) && username != "type") {
          let numbers = data[username];
          let n0 = numbers[0];
          let n1 = numbers[1];
          let n2 = numbers[2];

          let listItem = document.createElement("li");

          listItem.textContent = `${username}     wpm: ${n1} ${n2}`;

          progressList.appendChild(listItem);

          appendProgressBar(n0);
        }
      }
      break;

    case "newText":
      //        textElement.innerHTML = data['text'];
      text = data["text"];
      i = 0;
      characters = text.split("");
      inputtedString = "";
      totalCount = 0;

      slideText();
      break;

    case "gameOver":
      let gameOver = document.getElementById("game-over");
      gameOver.innerHTML = "The game is over!";
      break;
  }
});

function updateAccuracy() {
  accuracy = correct / (correct + incorrect);
  accuracyElement.textContent = `Accuracy: ${accuracy.toFixed(2) * 100}%`;
}

function updateServer() {
  socket.send(
    JSON.stringify({
      type: "playerUpdate",
      correct: correct,
      incorrect: incorrect,
    }),
  );
}

function updateCountdown() {
  document.getElementById("countdown").innerText = countdownValue;
  countdownValue--;

  if (countdownValue < 0) {
    clearInterval(timer);
    document.getElementById("countdown").innerText = "Go!!!";
    window.addEventListener("keydown", handleKey);
    setInterval(updateServer, 500);
  }
}

function slideText() {
  let slice = characters.slice(
    Math.max(0, i - 5),
    Math.min(characters.length, i + 105),
  );
  textElement.innerHTML = slice.join("");
}

function appendProgressBar(percentage) {
  percentage = Math.max(0, Math.min(100, percentage));

  var ul = document.getElementById("progress-list");
  var li = document.createElement("li");
  var divProgress = document.createElement("div");
  divProgress.className = "progress-container";
  var divBar = document.createElement("div");
  divBar.className = "progress-bar";
  divBar.style.width = percentage + "%"; // Set initial width
  //  divBar.innerText = percentage + "%"; // Display progress percentage

  var imgReindeer = document.createElement("img");
  imgReindeer.src = "../../static/reindeer.png";
  imgReindeer.alt = "Reindeer";
  imgReindeer.className = "reindeer-image";

  divProgress.appendChild(divBar);
  divProgress.appendChild(imgReindeer);
  li.appendChild(divProgress);
  ul.appendChild(li);

  var divProgressWidth = divProgress.offsetWidth;
  var imgReindeerWidth = imgReindeer.offsetWidth;
  var reindeerPosition =
    (percentage / 100) * divProgressWidth - imgReindeerWidth;
  imgReindeer.style.left = reindeerPosition + "px";
}

// Initial call to update countdown
updateCountdown();

// Update the countdown every second
const timer = setInterval(updateCountdown, 1000);
