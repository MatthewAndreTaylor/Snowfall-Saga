const canvas = document.getElementById("snowfall");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let snowflakes = [];

function setCanvasSize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

// Create snowflakes
function createSnowflakes() {
  snowflakes = [];
  for (let i = 0; i < 50; i++) {
    snowflakes.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      opacity: Math.random(),
      speedX: (Math.random() - 0.5) * 5,
      speedY: Math.random() + 1,
      radius: Math.random() * 5 + 1,
    });
  }
}

function drawSnowflakes() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "rgba(200, 200, 255, 0.8)";
  ctx.beginPath();
  for (let flake of snowflakes) {
    ctx.moveTo(flake.x, flake.y);
    ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
  }
  ctx.fill();
}

function moveSnowflakes() {
  for (let flake of snowflakes) {
    flake.x += flake.speedX;
    flake.y += flake.speedY;

    if (flake.y > canvas.height) {
      flake.x = Math.random() * canvas.width;
      flake.y = -flake.radius * 2;
    }
  }
}

function updateSnowfall() {
  moveSnowflakes();
  drawSnowflakes();
  requestAnimationFrame(updateSnowfall);
}

window.addEventListener("resize", () => {
  setCanvasSize();
  createSnowflakes();
});

setCanvasSize();
createSnowflakes();
updateSnowfall();
