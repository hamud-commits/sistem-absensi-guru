(() => {
  const btn = document.getElementById('btnToggleSidebar');
  const sidebar = document.querySelector('.sidebar');
  if (btn && sidebar) {
    btn.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
})();

