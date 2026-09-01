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

// ── Keep the message when the send fails ──────────────────────────────────
//
// /contact/problem is a static page, so it cannot be handed the submitted
// values: the function answers with a redirect, and putting a stranger's
// message in a URL would leak it into history and every log along the way.
// So the browser keeps its own copy, in sessionStorage, and only for as long
// as the tab is open.
const KEY = 'contact-draft';

if (form) {
  form.addEventListener('submit', () => {
    try {
      const data = new FormData(form);
      sessionStorage.setItem(
        KEY,
        JSON.stringify({
          name: data.get('name') || '',
          email: data.get('email') || '',
          message: data.get('message') || '',
        }),
      );
    } catch {
      // Private mode, or storage disabled. The form still submits.
    }
  });
}

// On the failure page, turn the draft into a prefilled email so the retry is a
// click rather than a retype. On the success page, drop it — the message is
// sent, and keeping a copy around serves nobody.
const rescue = document.querySelector('[data-rescue]');
const sent = document.querySelector('[data-sent]');

try {
  if (sent) {
    sessionStorage.removeItem(KEY);
  } else if (rescue) {
    const draft = JSON.parse(sessionStorage.getItem(KEY) || 'null');
    if (draft && (draft.name || draft.message)) {
      const body = `Name:\n${draft.name}\n\nWhat you are working on (one line):\n${draft.message}\n`;
      rescue.href = `${rescue.dataset.rescue}?subject=${encodeURIComponent(
        'Introduction',
      )}&body=${encodeURIComponent(body)}`;
      rescue.textContent = 'Email me directly — your message is already in it';
    }
  }
} catch {
  // Nothing stored, or unreadable. The plain mailto link still works.
}
