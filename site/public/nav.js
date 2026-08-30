// Served from /public so the CSP can stay on `script-src 'self'` — an Astro
// <script> gets inlined into the HTML, which would need a hash per build.
const header = document.querySelector('[data-nav]');
const burger = header?.querySelector('[data-burger]');
const menu = document.getElementById('site-menu');

if (header && burger && menu) {
  burger.hidden = false;
  header.dataset.js = '';

  const setOpen = (open) => {
    header.toggleAttribute('data-open', open);
    burger.setAttribute('aria-expanded', String(open));
  };

  const close = (refocus = false) => {
    if (!header.hasAttribute('data-open')) return;
    setOpen(false);
    if (refocus) burger.focus();
  };

  burger.addEventListener('click', () => {
    setOpen(!header.hasAttribute('data-open'));
  });

  // A tapped link navigates, but same-page anchors do not — close either way.
  menu.addEventListener('click', (e) => {
    if (e.target.closest('a')) close();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close(true);
  });

  document.addEventListener('pointerdown', (e) => {
    if (!header.contains(e.target)) close();
  });

  // Leaving the mobile breakpoint with the panel open would strand the state.
  const wide = window.matchMedia('(min-width: 641px)');
  wide.addEventListener('change', (e) => {
    if (e.matches) close();
  });
}
