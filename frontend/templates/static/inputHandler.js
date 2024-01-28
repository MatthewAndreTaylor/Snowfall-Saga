addEventListener("keydown", function (event) {
  if (clicked) return;  

  if (event.code == "KeyD") vxr = speed;
  if (event.code == "KeyA") vxl = -speed;
  if (event.code == "KeyS") vyd = speed;
  if (event.code == "KeyW") vyu = -speed;
});

addEventListener("keyup", function (event) {
  if (clicked) return;

  if (event.code == "KeyD") vxr = 0;
  if (event.code == "KeyA") vxl = 0;
  if (event.code == "KeyS") vyd = 0;
  if (event.code == "KeyW") vyu = 0;
});

addEventListener("mousedown", function (event) {
  clicked = true;

  mouseX = event.clientX;
  mouseY = event.clientY;

  const deltaX = mouseX - x - mouseXOffset;
  const deltaY = mouseY - y - mouseYOffset;

  const angle = Math.atan2(deltaY, deltaX);

  vxr = speed * Math.cos(angle);
  vyd = speed * Math.sin(angle);
});
