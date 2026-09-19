document.addEventListener("DOMContentLoaded", () => {
  const flash = document.querySelector(".flash-wrap");
  if (flash) setTimeout(() => flash.style.opacity = "0", 3500);
});
