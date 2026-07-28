SGC Deal Scout — encrypted live dashboard.

Published at https://javad-SOLID.github.io/sredeal/ (passphrase required).

This repository is public because GitHub Pages requires it on the free tier, so
index.html contains ONLY an unlock page plus AES-256-GCM ciphertext. The dashboard
is decrypted in the browser; the passphrase never leaves the device and never
appears in this repo.

index.html is regenerated every weekday morning (~6:00 AM PT) by the scheduled
SGC Deal Scout sweep, which decrypts it, merges the new sweep, and re-encrypts it.
Do not hand-edit index.html — use build.py.

  python3 build.py decrypt --in index.html --out dashboard.html --password "..."
  python3 build.py encrypt --in dashboard.html --out index.html --password "..."

dashboard.html is the plaintext working copy and is git-ignored. Never commit it.
