from __future__ import annotations

from html import escape


def render_login_page(
    login_url: str,
    next_url: str,
    error_message: str | None = None,
    brand_name: str = 'WiFi Access',
    support_message: str | None = None,
) -> str:
    safe_login_url = escape(login_url, quote=True)
    safe_next_url = escape(next_url, quote=True)
    safe_brand_name = escape(brand_name)
    safe_support_message = escape(support_message) if support_message else ''
    safe_error_message = escape(error_message) if error_message else ''
    support_html = f'<p class="support">{safe_support_message}</p>' if support_message else ''
    error_html = f'<div class="alert" role="alert" aria-live="assertive">{safe_error_message}</div>' if error_message else ''

    return f'''<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f0f9ff">
  <title>Login WiFi — {safe_brand_name}</title>
  <style>
    :root {{
      --sky-50: #f0f9ff;
      --sky-100: #e0f2fe;
      --sky-200: #bae6fd;
      --sky-500: #0ea5e9;
      --sky-600: #0284c7;
      --sky-700: #0369a1;
      --ink: #0f172a;
      --muted: #64748b;
      --white: #ffffff;
    }}

    * {{ box-sizing: border-box; }}

    body.page {{
      min-height: 100dvh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 24px;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 18%, rgba(14, 165, 233, .14) 0, transparent 28%),
        radial-gradient(circle at 88% 82%, rgba(56, 189, 248, .16) 0, transparent 30%),
        linear-gradient(180deg, var(--white) 0%, var(--sky-50) 100%);
    }}

    .card {{
      width: min(420px, 100%);
      padding: 36px;
      background: var(--white);
      border: 1px solid var(--sky-100);
      border-radius: 28px;
      box-shadow: 0 24px 70px rgba(14, 165, 233, .13);
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 28px;
    }}

    .brand-icon {{
      width: 46px;
      height: 46px;
      display: grid;
      place-items: center;
      border-radius: 16px;
      color: var(--white);
      background: linear-gradient(135deg, var(--sky-500), var(--sky-600));
      box-shadow: 0 12px 24px rgba(14, 165, 233, .22);
    }}

    .brand-title {{
      margin: 0;
      font-size: 22px;
      line-height: 1.25;
      font-weight: 800;
      letter-spacing: -.02em;
    }}

    .brand-subtitle {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.4;
    }}

    .alert {{
      margin-bottom: 20px;
      padding: 12px 14px;
      border: 1px solid #fecaca;
      border-radius: 14px;
      background: #fef2f2;
      color: #991b1b;
      font-size: 14px;
      line-height: 1.4;
    }}

    .field {{
      margin-bottom: 20px;
    }}

    .label {{
      display: block;
      margin-bottom: 8px;
      color: #334155;
      font-size: 14px;
      font-weight: 700;
    }}

    .input {{
      width: 100%;
      min-height: 52px;
      padding: 0 16px;
      border: 1px solid var(--sky-200);
      border-radius: 16px;
      background: #fbfeff;
      color: var(--ink);
      font-size: 16px;
      transition: border-color .18s ease, box-shadow .18s ease, background-color .18s ease;
    }}

    .input:focus {{
      outline: 0;
      border-color: var(--sky-500);
      background: var(--white);
      box-shadow: 0 0 0 4px rgba(14, 165, 233, .14);
    }}

    .password-wrap {{
      position: relative;
      display: grid;
    }}

    .password-wrap .input {{
      padding-right: 58px;
    }}

    .password-toggle {{
      position: absolute;
      top: 8px;
      right: 8px;
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      border: 0;
      border-radius: 12px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      transition: background-color .18s ease, color .18s ease;
    }}

    .password-toggle:hover,
    .password-toggle:focus-visible {{
      color: var(--sky-600);
      background: var(--sky-50);
      outline: 0;
    }}

    .submit {{
      width: 100%;
      min-height: 54px;
      margin-top: 6px;
      border: 0;
      border-radius: 18px;
      color: var(--white);
      font-size: 16px;
      font-weight: 800;
      cursor: pointer;
      background: linear-gradient(135deg, var(--sky-500), var(--sky-600));
      box-shadow: 0 14px 28px rgba(14, 165, 233, .24);
      transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
    }}

    .submit:hover {{
      transform: translateY(-1px);
      filter: brightness(1.04);
      box-shadow: 0 18px 34px rgba(14, 165, 233, .28);
    }}

    .submit:focus-visible,
    .input:focus-visible {{
      outline: 3px solid rgba(14, 165, 233, .38);
      outline-offset: 2px;
    }}

    .submit:disabled {{
      cursor: not-allowed;
      opacity: .72;
      transform: none;
    }}

    .support {{
      margin: 22px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      text-align: center;
    }}

    @media (max-width: 380px) {{
      .card {{ padding: 28px 22px; border-radius: 24px; }}
      .brand {{ margin-bottom: 22px; }}
    }}
  </style>
</head>
<body class="page">
  <main class="card" aria-labelledby="page-title">
    <header class="brand">
      <div class="brand-icon" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
          <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
          <path d="M8.53 15.11a6 6 0 0 1 6.95 0"/>
          <circle cx="12" cy="20" r="1" fill="currentColor"/>
        </svg>
      </div>
      <div>
        <h1 class="brand-title" id="page-title">{safe_brand_name}</h1>
        <p class="brand-subtitle">Masukkan username &amp; password dari transaksi Anda</p>
      </div>
    </header>

    {error_html}

    <form id="login-form" method="post" action="{safe_login_url}">
      <div class="field">
        <label class="label" for="username">Username</label>
        <input class="input" id="username" name="username" type="text" inputmode="text" autocapitalize="none" autocomplete="username" spellcheck="false" required>
      </div>

      <div class="field">
        <label class="label" for="password">Password</label>
        <div class="password-wrap">
          <input class="input" id="password" name="password" type="password" autocomplete="current-password" required>
          <button class="password-toggle" id="password-toggle" type="button" aria-controls="password" aria-label="Tampilkan password" aria-pressed="false" data-visible-label="Sembunyikan" data-hidden-label="Tampilkan">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
      </div>

      <input type="hidden" name="dst" value="{safe_next_url}">
      <input type="hidden" name="popup" value="true">
      <button class="submit" id="submit-button" type="submit" data-loading-label="Memproses...">Masuk</button>
    </form>

    {support_html}
  </main>

  <script>
    (function() {{
      const form = document.getElementById('login-form');
      const password = document.getElementById('password');
      const toggle = document.getElementById('password-toggle');
      const submitButton = document.getElementById('submit-button');
      const visibleIcon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
      const hiddenIcon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-2.29 3.19"/><path d="M6.61 6.61A17.32 17.32 0 0 0 2 12s3.5 7 10 7a10.74 10.74 0 0 0 5.39-1.39"/><path d="m2 2 20 20"/><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/></svg>';

      toggle.addEventListener('click', function() {{
        const isVisible = password.type === 'text';
        password.type = isVisible ? 'password' : 'text';
        toggle.innerHTML = isVisible ? visibleIcon : hiddenIcon;
        toggle.setAttribute('aria-pressed', String(!isVisible));
        toggle.setAttribute('aria-label', isVisible ? toggle.dataset.hiddenLabel + ' password' : toggle.dataset.visibleLabel + ' password');
      }});

      form.addEventListener('submit', function() {{
        submitButton.disabled = true;
        submitButton.textContent = submitButton.dataset.loadingLabel;
      }});
    }})();
  </script>
</body>
</html>'''


def render_mikrotik_login_page(
    brand_name: str = 'WiFi Access',
    support_message: str | None = None,
) -> str:
    pap_page = render_login_page(
        login_url='$(link-login-only)',
        next_url='$(link-orig)',
        error_message='__MIKROTIK_ERROR_BLOCK__',
        brand_name=brand_name,
        support_message=support_message,
    )
    error_block = (
        '$(if error)'
        '<div class="alert" role="alert" aria-live="assertive">$(error)</div>'
        '$(endif)'
    )
    return pap_page.replace(
        '<div class="alert" role="alert" aria-live="assertive">__MIKROTIK_ERROR_BLOCK__</div>',
        error_block,
    )
