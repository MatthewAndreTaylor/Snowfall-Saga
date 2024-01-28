addEventListener("keydown", function (event) {
  vxr = 0;
  vxl = 0;
  vyd = 0;
  vyu = 0;
  if (event.code == "KeyD") vxr = speed;
  if (event.code == "KeyA") vxl = -speed;
  if (event.code == "KeyS") vyd = speed;
  if (event.code == "KeyW") vyu = -speed;
});

addEventListener("keyup", function (event) {
  if (event.code == "KeyD") vxr = 0;
  if (event.code == "KeyA") vxl = 0;
  if (event.code == "KeyS") vyd = 0;
  if (event.code == "KeyW") vyu = 0;
});

addEventListener("mousedown", function (event) {
  mouseX = event.clientX;
  mouseY = event.clientY;
  const deltaX = mouseX - x;
  const deltaY = mouseY - y;
  const angle = Math.atan2(deltaY, deltaX);
  vxr = speed * Math.cos(angle);
  vyd = speed * Math.sin(angle);
});
