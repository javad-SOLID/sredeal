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

---

## investors/ — Solid Ground Capital investor portal

Published at https://javad-SOLID.github.io/sredeal/investors/ (login required).

Same principle as the dashboard: the repo is public, so nothing is stored in
plaintext. investors/index.html holds one AES-256-GCM catalogue blob (deals,
projects, fund figures) plus one encrypted vault per member. A member's vault is
sealed under their own passphrase and carries a copy of the catalogue key, so
each member can read the shared catalogue and their own holdings and nobody
else's.

  python3 portal_build.py catalog-get --in investors/index.html --out catalog.json --key "$CK"
  python3 portal_build.py catalog-set --in investors/index.html --catalog catalog.json --out investors/index.html --key "$CK"
  python3 portal_build.py add-investor --in investors/index.html --out investors/index.html --key "$CK" \
      --roster-entry '{"username":"...","name":"...", ...}' --password '...'
  python3 portal_build.py list-investors --in investors/index.html

catalog.json, roster.json and creds.json are git-ignored — they are the
plaintext forms and must never be committed.

## deck/ — investor presentation

Published at https://javad-SOLID.github.io/sredeal/deck/ — 21 slides, arrow-key or
click navigation, live cost-advantage toggle and deal calculator, press P to print.
A rendered PDF sits alongside it at deck/SGC-Investor-Presentation.pdf.

Unlike the dashboard and the portal this file is NOT encrypted, because it is meant
to be sent to prospective investors. It contains no exact addresses (block level
only), no investor names and no portfolio data. It is marked noindex.

To regenerate the PDF after editing deck/index.html, print it to PDF at 1280x720
with background graphics enabled.
