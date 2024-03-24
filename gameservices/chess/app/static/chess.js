let gameId = sessionStorage.getItem("gameId");

if (gameId === null) {
  document.getElementById("status").innerText =
    "Could not find a game to connect to.";
}

const socket = new WebSocket(
  `ws://${document.domain}:${location.port}/chess/game/${gameId}`,
);

let selectedSquare = null;

socket.addEventListener("open", (event) => {
  socket.send(
    JSON.stringify({
      type: "username",
      username: sessionStorage.getItem("username"),
    }),
  );
});

function squareClicked(squareId) {
  if (selectedSquare === null) {
    selectedSquare = squareId;
    console.log(squareId);
    document.getElementById(squareId).style.backgroundColor = "red"; // Change background color to red
  } else {
    make_move(selectedSquare, squareId);
    selectedSquare = null;
  }
}

function make_move(startSquare, endSquare) {
  // Reset all squares' background colors
  document.getElementById(startSquare).style.backgroundColor = document
    .getElementById(startSquare)
    .classList.contains("light")
    ? "#f0d9b5"
    : "#b58863";

  // This is where you can handle the move logic
  console.log("Move from " + startSquare + " to " + endSquare);
  if (startSquare === endSquare) {
    return;
  }
  socket.send(
    JSON.stringify({
      type: "makeMove",
      move: startSquare + endSquare,
    }),
  );
}

document.body.addEventListener("click", function (event) {
  if (!event.target.closest(".chessboard div")) {
    // Reset selectedSquare and restore normal colors of all squares

    if (selectedSquare != null) {
      document.getElementById(selectedSquare).style.backgroundColor = document
        .getElementById(selectedSquare)
        .classList.contains("light")
        ? "#f0d9b5"
        : "#b58863";
    }
    selectedSquare = null;
  }
});


function displayChessBoard(chessBoardString) {
  // Split the string representation into rows
  const rows = chessBoardString.trim().split("\n");

  const chessboardElement = document.getElementById("chessboard");
  chessboardElement.innerHTML = ""; // Clear previous content

  rows.forEach((row, rowIndex) => {
    // Split each row into individual squares
    const squares = row.trim().split(" ");

    squares.forEach((piece, colIndex) => {
      const squareId = String.fromCharCode(97 + colIndex) + (8 - rowIndex);
      const squareElement = document.createElement("div");
      squareElement.id = squareId;
      squareElement.className =
        (rowIndex + colIndex) % 2 === 0 ? "light" : "dark";

      // Create an image element for the piece
      const pieceImg = document.createElement("img");
      if (piece !== ".") {
        const pieceFilename =
          piece === piece.toUpperCase() ? `${piece}w.png` : `${piece}b.png`;
        pieceImg.src = `../../static/${pieceFilename}`;
        pieceImg.alt = piece; // Set alt text to the piece representation
      }

      // Append the piece image to the square element
      squareElement.appendChild(pieceImg);

      // Attach event listener to the square element
      squareElement.addEventListener("click", () => squareClicked(squareId));

      // Append the square element to the chessboard
      chessboardElement.appendChild(squareElement);
    });
  });
}

function startTimer(seconds, container, oncomplete) {
  var startTime,
    timer,
    obj,
    ms = seconds * 1000,
    display = document.getElementById(container);
  obj = {};
  obj.resume = function () {
    startTime = new Date().getTime();
    timer = setInterval(obj.step, 250); // adjust this number to affect granularity
    // lower numbers are more accurate, but more CPU-expensive
  };
  obj.pause = function () {
    ms = obj.step();
    clearInterval(timer);
  };
  obj.step = function () {
    var now = Math.max(0, ms - (new Date().getTime() - startTime)),
      m = Math.floor(now / 60000),
      s = Math.floor(now / 1000) % 60;
    s = (s < 10 ? "0" : "") + s;
    display.innerHTML = m + ":" + s;
    if (now == 0) {
      clearInterval(timer);
      obj.resume = function () {};
      if (oncomplete) oncomplete();
    }
    return now;
  };
  obj.resume();
  return obj;
}

var timer;

let timerStarted = false;

function setPlayerNames(player1Name, player2Name) {
  document.getElementById("player1").textContent = player1Name;
  document.getElementById("player2").textContent = player2Name;
}

socket.addEventListener("message", (message) => {
  const data = JSON.parse(message.data);

  switch (data.type) {
    case "board":
      displayChessBoard(data.board);
      document.getElementById("status").innerText = "";
      break;

    case "message":
      document.getElementById("status").innerText = data.message;
      break;

    case "yourTurn":
      if (!timerStarted) {
        timer = startTimer(5 * 60, "timer", function () {
          socket.send(
            JSON.stringify({
              type: "timeUp",
            }),
          );
        });
        timerStarted = true;
      } else {
        timer.resume();
      }
      break;

    case "notYourTurn":
      timer.pause();
      break;

    case "usernames":
      let player1 = data.player1;
      let player2 = "Waiting for Player 2...";
      if (data.player2.length > 0) {
        player2 = data.player2;
      }
      setPlayerNames(player1, player2);
      break;
  }
});
