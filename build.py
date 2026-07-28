#!/usr/bin/env python3
"""
SGC Deal Scout — passphrase gate build tool.

The repo is public (GitHub Pages requires it on the free tier), so the dashboard
is stored ENCRYPTED. index.html contains only a small unlock page plus AES-256-GCM
ciphertext; the real dashboard never exists in plaintext in this repository.

  Decrypt (start of a sweep):
      python3 build.py decrypt --in index.html --out dashboard.html --password 'PASSPHRASE'

  Encrypt (end of a sweep):
      python3 build.py encrypt --in dashboard.html --out index.html --password 'PASSPHRASE'

dashboard.html is git-ignored. Never commit it.

Crypto: PBKDF2-HMAC-SHA256, 600000 iterations, 16-byte random salt, AES-256-GCM
with a 12-byte random IV. Payload layout is salt || iv || ciphertext+tag, base64.
The browser side uses WebCrypto with identical parameters.
"""

import argparse
import base64
import os
import re
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600000
SALT_LEN = 16
IV_LEN = 12

PAYLOAD_RE = re.compile(
    r'<script type="application/octet-stream" id="payload">\s*(.*?)\s*</script>',
    re.DOTALL,
)


def derive(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


GATE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>SGC Deal Scout</title>
<style>
  :root {
    color-scheme: light;
    --page: #f9f9f7; --surface: #fcfcfb; --ink-1: #0b0b0b; --ink-2: #52514e;
    --ink-muted: #898781; --border: rgba(11,11,11,0.12); --baseline: #c3c2b7;
    --accent: #2a78d6; --critical: #d03b3b;
  }
  @media (prefers-color-scheme: dark) {
    :root { color-scheme: dark; --page:#0d0d0d; --surface:#1a1a19; --ink-1:#fff;
            --ink-2:#c3c2b7; --border:rgba(255,255,255,0.12); --baseline:#383835;
            --accent:#3987e5; }
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         background: var(--page); color: var(--ink-1);
         min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
  .box { background: var(--surface); border:1px solid var(--border); border-radius:12px;
         padding:28px 26px; width:100%; max-width:380px; }
  h1 { font-size:19px; font-weight:700; }
  .sub { font-size:13px; color:var(--ink-2); margin-top:6px; line-height:1.5; }
  form { margin-top:20px; }
  label { display:block; font-size:11px; color:var(--ink-2); margin-bottom:5px;
          text-transform:uppercase; letter-spacing:.05em; font-weight:650; }
  input { width:100%; font:inherit; font-size:16px; padding:10px 12px;
          border:1px solid var(--baseline); border-radius:8px;
          background: var(--page); color: var(--ink-1); }
  input:focus { outline:2px solid var(--accent); outline-offset:0; border-color:transparent; }
  button { width:100%; margin-top:12px; font:inherit; font-size:14px; font-weight:650;
           padding:11px; border-radius:8px; border:1px solid var(--accent);
           background: var(--accent); color:#fff; cursor:pointer; }
  button:disabled { opacity:.6; cursor:default; }
  .msg { font-size:12.5px; margin-top:12px; min-height:18px; line-height:1.45; }
  .msg.err { color: var(--critical); font-weight:650; }
  .msg.wait { color: var(--ink-2); }
  .fine { font-size:11px; color:var(--ink-muted); margin-top:18px; line-height:1.5;
          border-top:1px solid var(--border); padding-top:12px; }
</style>
</head>
<body>
<div class="box">
  <h1>SGC Deal Scout</h1>
  <div class="sub">Solid Ground Construction &middot; LA County + Inland Empire deal dashboard. Enter the passphrase to unlock.</div>
  <form id="f" autocomplete="on">
    <label for="pw">Passphrase</label>
    <input id="pw" name="password" type="password" autocomplete="current-password"
           autocapitalize="off" autocorrect="off" spellcheck="false" required>
    <button id="go" type="submit">Unlock</button>
  </form>
  <div class="msg" id="msg"></div>
  <div class="fine">This page is encrypted. The dashboard is decrypted in your browser &mdash; the passphrase is never sent anywhere.</div>
</div>

<script type="application/octet-stream" id="payload">__PAYLOAD__</script>

<script>
(function () {
  var ITER = __ITER__, SALT_LEN = __SALT_LEN__, IV_LEN = __IV_LEN__;
  var msg = document.getElementById('msg');
  var btn = document.getElementById('go');

  function b64ToBytes(b64) {
    var bin = atob(b64.replace(/\\s+/g, ''));
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  document.getElementById('f').addEventListener('submit', function (e) {
    e.preventDefault();
    var pw = document.getElementById('pw').value;
    if (!pw) return;
    btn.disabled = true;
    msg.className = 'msg wait';
    msg.textContent = 'Decrypting\\u2026';

    var raw = document.getElementById('payload').textContent;
    var bytes = b64ToBytes(raw);
    var salt = bytes.slice(0, SALT_LEN);
    var iv = bytes.slice(SALT_LEN, SALT_LEN + IV_LEN);
    var ct = bytes.slice(SALT_LEN + IV_LEN);
    var enc = new TextEncoder();

    crypto.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveKey'])
      .then(function (km) {
        return crypto.subtle.deriveKey(
          { name: 'PBKDF2', salt: salt, iterations: ITER, hash: 'SHA-256' },
          km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
      })
      .then(function (key) {
        return crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, ct);
      })
      .then(function (buf) {
        var html = new TextDecoder().decode(buf);
        document.open();
        document.write(html);
        document.close();
      })
      .catch(function () {
        btn.disabled = false;
        msg.className = 'msg err';
        msg.textContent = 'Wrong passphrase \\u2014 try again.';
        document.getElementById('pw').select();
      });
  });
})();
</script>
</body>
</html>
"""


def cmd_encrypt(args):
    plaintext = open(args.infile, "rb").read()
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    key = derive(args.password, salt)
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    payload = base64.b64encode(salt + iv + ct).decode("ascii")
    # wrap so git diffs stay sane
    wrapped = "\n".join(payload[i:i + 120] for i in range(0, len(payload), 120))
    html = (GATE_TEMPLATE
            .replace("__PAYLOAD__", wrapped)
            .replace("__ITER__", str(ITERATIONS))
            .replace("__SALT_LEN__", str(SALT_LEN))
            .replace("__IV_LEN__", str(IV_LEN)))
    open(args.outfile, "w", encoding="utf-8").write(html)
    print("encrypted %d bytes -> %s (%d bytes)"
          % (len(plaintext), args.outfile, len(html)))


def cmd_decrypt(args):
    html = open(args.infile, "r", encoding="utf-8").read()
    m = PAYLOAD_RE.search(html)
    if not m:
        sys.exit("ERROR: no encrypted payload found in %s. Is it already plaintext?"
                 % args.infile)
    bytes_ = base64.b64decode(re.sub(r"\s+", "", m.group(1)))
    salt, iv, ct = bytes_[:SALT_LEN], bytes_[SALT_LEN:SALT_LEN + IV_LEN], bytes_[SALT_LEN + IV_LEN:]
    key = derive(args.password, salt)
    try:
        plaintext = AESGCM(key).decrypt(iv, ct, None)
    except Exception:
        sys.exit("ERROR: decryption failed — wrong passphrase?")
    open(args.outfile, "wb").write(plaintext)
    print("decrypted -> %s (%d bytes)" % (args.outfile, len(plaintext)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("encrypt", cmd_encrypt), ("decrypt", cmd_decrypt)):
        s = sub.add_parser(name)
        s.add_argument("--in", dest="infile", required=True)
        s.add_argument("--out", dest="outfile", required=True)
        s.add_argument("--password", required=True)
        s.set_defaults(func=fn)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
