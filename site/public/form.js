// Progressive enhancement for the contact form. The form works without this
// file — it is a plain POST — so everything here is guarded and optional.
//
// Served from /public rather than an Astro <script> so the CSP can stay on
// `script-src 'self'`; an inlined script would need a hash per build.
const form = document.querySelector('[data-contact-form]');

if (form) {
  const button = form.querySelector('button[type="submit"]');
  let submitting = false;

  form.addEventListener('submit', (e) => {
    // A second click before the first response lands would send a second email.
    // The 303 stops a refresh resending; nothing stopped an impatient click.
    if (submitting) {
      e.preventDefault();
      return;
    }
    submitting = true;

    // Disabling during the submit event would cancel the submission in some
    // browsers, so hand control back first and disable on the next tick.
    setTimeout(() => {
      if (button) {
        button.disabled = true;
        button.textContent = 'Sending…';
      }
    }, 0);
  });
}
