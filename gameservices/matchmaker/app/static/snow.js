document.addEventListener("DOMContentLoaded", () => {
  const snowflakeCount = 200;

  for (let i = 0; i < snowflakeCount; i++) {
    createSnowflake();
  }

  function createSnowflake() {
    const snowflake = document.createElement("div");
    let content = document.createTextNode("❄");
    snowflake.appendChild(content);
    snowflake.className = "snowflake";
    snowflake.style.fontSize = `calc(6px + ${Math.random() * 7}px)`;
    snowflake.style.left = `${Math.random() * 90}vw`;
    snowflake.style.animation = `
            snowflake-fall ${6 + 6 * Math.random()}s linear ${
              1 + 4 * Math.random()
            }s infinite normal,
            snowflake-shake ${8 + 6 * Math.random()}s ease-in-out ${
              1 + 4 * Math.random()
            }s infinite alternate,
            snowflake-wind-w ${6 + 6 * Math.random()}s linear ${
              1 + 4 * Math.random()
            }s infinite normal
        `;

    document.body.appendChild(snowflake);
  }
});
