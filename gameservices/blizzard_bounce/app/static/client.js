const width = 800;
const height = 1000;
const two = new Two({
  width: width,
  height: height,
  autostart: true,
}).appendTo(document.body);

// Send the user back to lobby
document.addEventListener("DOMContentLoaded", function () {
  const lobbyButton = document.getElementById("lobbyButton");
  lobbyButton.addEventListener("click", function () {
    window.location.href = "http://127.0.0.1:5000/";
  });
});

const borderWidth = 5;
const border = two.makeRectangle(width / 2, height / 2, width, height);
border.linewidth = borderWidth;
border.stroke = "black";

// Add the rectangle to the scene
two.add(border);

const topGoal = two.makeRectangle(width / 2, 15, width / 3, 30);
topGoal.fill = "purple";
topGoal.noStroke();

const bottomGoal = two.makeRectangle(width / 2, height - 15, width / 3, 30);
bottomGoal.fill = "purple";
bottomGoal.noStroke();

let my_id = Math.random().toString(36).substring(7);
console.log(my_id);

// Define a function to create a circle shape in Two.js
function createCircle(x, y, radius, color) {
  const circle = two.makeCircle(x, y, radius);
  circle.fill = color;
  circle.noStroke();
  return circle;
}

// Track player circle
let player0 = {};
let player1 = {};
let balls = {};

function tweenPlayerCircle(player, x, y) {
  new TWEEN.Tween(player.translation)
    .to({ x, y }, 1) // Adjust the duration as needed
    .start();
}

// Update other circles (balls) with tween animation
function tweenBall(ball, x, y) {
  new TWEEN.Tween(ball.translation)
    .to({ x, y }, 1) // Adjust the duration as needed
    .start();
}

// Connect to the WebSocket for receiving game state
const socket = new WebSocket(`ws://${location.host}/echo`);

socket.addEventListener("open", (event) => {
  console.log("Connected to server: ", event);
});

socket.addEventListener("message", (event) => {
  try {
    const data = JSON.parse(event.data);

    // Update scores
    document.getElementById("blueScore").innerText = data.scores[0];
    document.getElementById("greenScore").innerText = data.scores[1];

    // Update player0's circle positions
    data.player0.forEach((playerData) => {
      let player = player0[playerData.id];
      if (!player) {
        player = createCircle(playerData.x, playerData.y, 30, "blue");
        player0[playerData.id] = player;
      } else {
        tweenPlayerCircle(player, playerData.x, playerData.y);
      }
    });

    // Update player1's circle positions
    data.player1.forEach((playerData) => {
      let player = player1[playerData.id];
      if (!player) {
        player = createCircle(playerData.x, playerData.y, 30, "green");
        player1[playerData.id] = player;
      } else {
        tweenPlayerCircle(player, playerData.x, playerData.y);
      }
    });

    // Update other circles (balls)
    data.balls.forEach((ballData) => {
      let ball = balls[ballData.id];
      if (!ball) {
        ball = createCircle(ballData.x, ballData.y, 20, "red");
        balls[ballData.id] = ball;
      } else {
        tweenBall(ball, ballData.x, ballData.y);
      }
    });

    // Remove any circles that are no longer in the game state
    Object.keys(balls).forEach((id) => {
      if (!data.balls[id]) {
        two.remove(balls[id]);
        delete balls[id];
      }
    });
  } catch (error) {
    console.error("Error parsing JSON:", error);
    console.error("Raw data:", event.data);
  }
});

socket.addEventListener("close", (event) => {
  console.log("Connection closed:", event);
});

// Send user input via WebSocket
const inputSocket = new WebSocket(`ws://${location.host}/input`);

inputSocket.addEventListener("message", (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.error) {
      console.log("Spectator mode:", data.error);
    }
  } catch (error) {
    console.error("Error parsing JSON:", error);
    console.error("Raw data:", event.data);
  }
});

document.addEventListener("keydown", (event) => {
  const impulse = { x: 0, y: 0 };

  switch (event.key) {
    case "ArrowUp":
      impulse.y = -10;
      break;
    case "ArrowDown":
      impulse.y = 10;
      break;
    case "ArrowLeft":
      impulse.x = -10;
      break;
    case "ArrowRight":
      impulse.x = 10;
      break;
  }

  inputSocket.send(JSON.stringify(impulse));
});

function animate() {
  requestAnimationFrame(animate);
  TWEEN.update();
}

animate();
