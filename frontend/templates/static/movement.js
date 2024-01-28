const canvas = document.getElementById("lobby");
const ctx = canvas.getContext("2d");

const speed = 3;

// positions
let x = 0;
let y = 0;

// velocities
let vxl = 0;
let vxr = 0;
let vyu = 0;
let vyd = 0;

function updatePosition() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  x += vxl + vxr;
  y += vyu + vyd;

  // check boundaries
  if (x < 0) x = 0;
  if (x > canvas.width - 200) x = canvas.width - 200;
  if (y < 0) y = 0;
  if (y > canvas.height - 100) y = canvas.height - 100;

  ctx.fillRect(x, y, 50, 50);
  requestAnimationFrame(updatePosition);
}

updatePosition();
