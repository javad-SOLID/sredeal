#!/usr/bin/env python3
"""
SGC Investor Portal — build and maintenance tool.

The portal is a single self-contained HTML file that works both as a Cowork
artifact and as a page on GitHub Pages. Because the repository is public, all
content is encrypted inside it:

  * one CATALOG blob  — deals, projects, fund figures. Encrypted with a random
    32-byte content key (CK) that every member's vault carries a copy of.
  * one VAULT per investor — that member's own profile, positions and
    distributions, encrypted under THEIR passphrase (PBKDF2-HMAC-SHA256,
    600k iterations) with a copy of CK inside.

So a member can read the shared catalogue and their own holdings, and cannot
read anybody else's. Revoking a member means dropping their vault and rotating
CK (`rotate-key`), which re-encrypts the catalogue so an old copy is useless.

Commands
  pack           --template T --catalog C --roster R --out O --key CK
  catalog-get    --in O --out C --key CK          (daily sweep reads this)
  catalog-set    --in O --catalog C --out O --key CK  (daily sweep writes this)
  add-investor   --in O --out O --key CK --roster-entry '<json>' --password P
  list-investors --in O
  newkey                                          (prints a fresh CK)
"""

import argparse, base64, json, os, re, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER, SALT_LEN, IV_LEN = 600000, 16, 12

VAULT_RE = re.compile(r'(<script type="application/json" id="vaults">)(.*?)(</script>)', re.DOTALL)
CAT_RE = re.compile(r'(<script type="application/octet-stream" id="catalog">)(.*?)(</script>)', re.DOTALL)

b64e = lambda b: base64.b64encode(b).decode("ascii")
b64d = lambda s: base64.b64decode(re.sub(r"\s+", "", s))


def derive(password, salt):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                      iterations=ITER).derive(password.encode("utf-8"))


def seal_vault(obj, password):
    salt, iv = os.urandom(SALT_LEN), os.urandom(IV_LEN)
    ct = AESGCM(derive(password, salt)).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    return {"s": b64e(salt), "i": b64e(iv), "c": b64e(ct)}


def seal_catalog(cat, ck):
    iv = os.urandom(IV_LEN)
    ct = AESGCM(b64d(ck)).encrypt(iv, json.dumps(cat, separators=(",", ":")).encode(), None)
    return "\n".join(lambda_wrap(b64e(iv + ct)))


def lambda_wrap(s, n=120):
    return [s[i:i + n] for i in range(0, len(s), n)]


def open_catalog(html, ck):
    m = CAT_RE.search(html)
    if not m:
        sys.exit("ERROR: no catalog block found")
    blob = b64d(m.group(2))
    try:
        return json.loads(AESGCM(b64d(ck)).decrypt(blob[:IV_LEN], blob[IV_LEN:], None))
    except Exception:
        sys.exit("ERROR: catalog decryption failed — wrong content key?")


def put_catalog(html, cat, ck):
    return CAT_RE.sub(lambda m: m.group(1) + seal_catalog(cat, ck) + m.group(3), html, count=1)


def get_vaults(html):
    m = VAULT_RE.search(html)
    return json.loads(m.group(2)) if m else {}


def put_vaults(html, vaults):
    payload = json.dumps(vaults, separators=(",", ":"))
    return VAULT_RE.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1)


# ── commands ───────────────────────────────────────────────────────────────
def cmd_newkey(a):
    print(b64e(os.urandom(32)))


def cmd_pack(a):
    html = open(a.template, encoding="utf-8").read()
    cat = json.load(open(a.catalog, encoding="utf-8"))
    roster = json.load(open(a.roster, encoding="utf-8"))
    vaults = {}
    for r in roster:
        pw = r.pop("password")
        r["ck"] = a.key
        vaults[r["username"].lower()] = seal_vault(r, pw)
    html = html.replace("__VAULTS__", json.dumps(vaults, separators=(",", ":")))
    html = html.replace("__CATALOG__", seal_catalog(cat, a.key))
    open(a.out, "w", encoding="utf-8").write(html)
    print("packed %d investor vault(s) + catalog -> %s (%d bytes)"
          % (len(vaults), a.out, len(html)))


def cmd_catalog_get(a):
    cat = open_catalog(open(a.infile, encoding="utf-8").read(), a.key)
    json.dump(cat, open(a.out, "w"), indent=1)
    print("catalog -> %s (%d deals, %d investor-ready)"
          % (a.out, len(cat["deals"]), len([d for d in cat["deals"] if d.get("investorReady")])))


def cmd_catalog_set(a):
    html = open(a.infile, encoding="utf-8").read()
    cat = json.load(open(a.catalog, encoding="utf-8"))
    open(a.out, "w", encoding="utf-8").write(put_catalog(html, cat, a.key))
    print("catalog written into %s" % a.out)


def cmd_add_investor(a):
    html = open(a.infile, encoding="utf-8").read()
    vaults = get_vaults(html)
    rec = json.loads(a.roster_entry)
    rec["ck"] = a.key
    vaults[rec["username"].lower()] = seal_vault(rec, a.password)
    open(a.out, "w", encoding="utf-8").write(put_vaults(html, vaults))
    print("added %s (%s); portal now has %d member(s)" % (rec["username"], rec.get("name", ""), len(vaults)))


def cmd_list(a):
    print("\n".join(sorted(get_vaults(open(a.infile, encoding="utf-8").read()).keys())) or "(none)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("newkey"); s.set_defaults(func=cmd_newkey)

    s = sub.add_parser("pack")
    s.add_argument("--template", required=True); s.add_argument("--catalog", required=True)
    s.add_argument("--roster", required=True); s.add_argument("--out", required=True)
    s.add_argument("--key", required=True); s.set_defaults(func=cmd_pack)

    s = sub.add_parser("catalog-get")
    s.add_argument("--in", dest="infile", required=True); s.add_argument("--out", required=True)
    s.add_argument("--key", required=True); s.set_defaults(func=cmd_catalog_get)

    s = sub.add_parser("catalog-set")
    s.add_argument("--in", dest="infile", required=True); s.add_argument("--catalog", required=True)
    s.add_argument("--out", required=True); s.add_argument("--key", required=True)
    s.set_defaults(func=cmd_catalog_set)

    s = sub.add_parser("add-investor")
    s.add_argument("--in", dest="infile", required=True); s.add_argument("--out", required=True)
    s.add_argument("--key", required=True); s.add_argument("--roster-entry", required=True)
    s.add_argument("--password", required=True); s.set_defaults(func=cmd_add_investor)

    s = sub.add_parser("list-investors")
    s.add_argument("--in", dest="infile", required=True); s.set_defaults(func=cmd_list)

    a = p.parse_args(); a.func(a)


if __name__ == "__main__":
    main()
