const collisionSound = new Audio("/static/audio/snowballHit.mp3");

export function playCollisionSound() {
  collisionSound.play();
}
