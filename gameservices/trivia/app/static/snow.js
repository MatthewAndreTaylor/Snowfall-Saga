function createSnowflake() {
  const snowflake = document.createElement("div");
  snowflake.className = "snowflake";
  snowflake.style.width = Math.random() * 10 + "px";
  snowflake.style.height = snowflake.style.width;
  snowflake.style.left = Math.random() * window.innerWidth + "px";
  document.getElementById("snowflakes").appendChild(snowflake);
}

for (let i = 0; i < 50; i++) {
  createSnowflake();
}

function animateSnowflakes() {
  const snowflakes = document.querySelectorAll(".snowflake");

  snowflakes.forEach((snowflake) => {
    const speed = Math.random() * 5 + 1;
    const startPosition = Math.random() * window.innerWidth;
    snowflake.style.left = startPosition + "px";
    snowflake.style.animation = `snowfall linear infinite ${speed}s`;
  });
}

animateSnowflakes();
