/**
 * POST /api/contact — the one dynamic thing on this site.
 *
 * A Cloudflare Pages Function: a small piece of code that runs on Cloudflare's
 * network, not in the visitor's browser. Everything else in `dist/` is a file
 * served as-is; this is the one route that receives something and acts on it.
 *
 * The contact form is a plain HTML form with no JavaScript, so the whole
 * exchange is one POST and one redirect. That is deliberate — a form that
 * depends on JS to reach the inbox is a form that silently fails.
 *
 * Environment (set in the Cloudflare Pages dashboard, never in the repo):
 *   RESEND_API_KEY  required — the secret that authorises the send
 *   CONTACT_TO      required — the inbox that receives it
 *   CONTACT_FROM    optional — defaults to Resend's shared sending address
 */

interface Env {
  RESEND_API_KEY?: string;
  CONTACT_TO?: string;
  CONTACT_FROM?: string;
}

interface PagesContext {
  request: Request;
  env: Env;
}

const MAX = { name: 120, email: 200, message: 200 } as const;

/** Good enough to catch typos; the real proof of an address is a reply to it. */
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/**
 * Send the browser to one of the two outcome pages. Always 303, so the browser
 * follows it with a GET and a refresh cannot resend the message.
 *
 * The outcome is a URL rather than a query string because the site is
 * statically built — there is no server rendering /contact per request that
 * could read `?sent=1` and vary the page.
 */
function outcome(request: Request, ok: boolean): Response {
  const path = ok ? '/contact/sent' : '/contact/problem';
  return Response.redirect(new URL(path, request.url).toString(), 303);
}

function field(form: FormData, key: string, limit: number): string {
  const raw = form.get(key);
  return typeof raw === 'string' ? raw.trim().slice(0, limit) : '';
}

async function handlePost(request: Request, env: Env): Promise<Response> {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return outcome(request, false);
  }

  // Honeypot. A real person never sees this field, so anything in it is a bot.
  // Answer as if it worked — a bot told it failed simply tries again.
  if (field(form, 'company', 200) !== '') return outcome(request, true);

  const name = field(form, 'name', MAX.name);
  const email = field(form, 'email', MAX.email);
  const message = field(form, 'message', MAX.message);

  if (!name || !message || !EMAIL.test(email)) return outcome(request, false);

  // Misconfiguration is not the sender's fault, and it must never look sent.
  if (!env.RESEND_API_KEY || !env.CONTACT_TO) return outcome(request, false);

  let sent: Response;
  try {
    sent = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: env.CONTACT_FROM ?? 'Portfolio contact <onboarding@resend.dev>',
        to: [env.CONTACT_TO],
        // The submitter's address goes here, never in `from` — putting it there
        // would be sending mail as them, which the receiving server distrusts.
        reply_to: email,
        subject: `Portfolio contact — ${name}`,
        text: [
          `Name:  ${name}`,
          `Email: ${email}`,
          '',
          message,
          '',
          '— sent from the contact form',
        ].join('\n'),
      }),
    });
  } catch {
    return outcome(request, false);
  }

  if (!sent.ok) {
    // Reaches the Pages function log, never the page: it can carry key detail.
    console.error(`resend ${sent.status}: ${await sent.text()}`);
    return outcome(request, false);
  }

  return outcome(request, true);
}

export const onRequest = async (context: PagesContext): Promise<Response> => {
  const { request, env } = context;
  if (request.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST' } });
  }
  return handlePost(request, env);
};
