// Setup a new socket connection
const storeSocket = new WebSocket(`ws://${location.host}/purchase`);

const spriteContainer = document.querySelector("#sprite-container");

// Loads information about all sprites to purchase
function loadSprites() {
  if (onSale.length === 0) {
    spriteContainer.innerHTML =
      "There's nothing else for sale!<br>Check back later!";
  } else {
    onSale.forEach((sprite) => {
      spriteContainer.innerHTML += `
            <div class="item-container">
                <div class="sprite" style="background-position-y: ${
                  sprite * -28
                }px;"></div>
                <div class="info-container">
                    <div class="sprite-name">Sprite #${sprite + 1}</div>
                    <button class="purchase" data-value="${sprite}">100 Points</button>
                </div>
            </div>
            `;
    });
  }
}

storeSocket.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  const purchaseButton = document.querySelector(
    `[data-value="${data.sprite}"]`,
  );

  switch (data.type) {
    case "purchaseSuccess":
      const pointsDisplay = document.querySelector("#points");
      pointsDisplay.innerText = data.points;

      purchaseButton.classList.remove("purchase");
      purchaseButton.classList.add("owned");
      purchaseButton.innerText = "Owned!";

      break;
    case "purchaseFailure":
      purchaseButton.classList.remove("purchase");
      purchaseButton.classList.add("no-purchase");
      purchaseButton.innerText = "Insufficient Funds!";
      setTimeout(() => {
        purchaseButton.classList.remove("no-purchase");
        purchaseButton.classList.add("purchase");
        purchaseButton.innerText = "100 Points";
      }, 1000);

      break;
  }
});

// Checks if a user wishes to purchase an item using event delegation
spriteContainer.addEventListener("click", (e) => {
  const target = e.target;
  if (target.classList.contains("purchase")) {
    const pendingPurchase = parseInt(target.getAttribute("data-value"));
    const message = {
      type: "purchase",
      sprite: pendingPurchase,
    };
    storeSocket.send(JSON.stringify(message));
  }
});

// Loads the sprites and their information
loadSprites();
