# SGC Command Center — iPad / web app

`index.html` is the installable Solid Ground Capital Command Center: Deal Scout,
leads, deals & underwriting, projects, crew, partners, loans, inspections,
investors, financials, and the communications hub.

**This copy ships with no data in it.** All records live only in the browser
storage of whichever device you install it on, encrypted with your passcode
(PBKDF2 → AES-GCM). Nothing is uploaded and nothing is stored in this repo.

## Install on an iPad or iPhone
1. Open https://javad-SOLID.github.io/sredeal/hub/ in **Safari**.
2. Tap **Share** → **Add to Home Screen** → **Add**.
3. Launch it from the home screen. Set a passcode when asked.
4. Move your data over: on the Mac open the Hub, tap **Save**, send the JSON to
   the iPad (AirDrop or Files), then in the app tap **Load** and pick it.

## Project files
The working copies of the Hub, dashboards and planning docs live in Google Drive:
My Drive → Claude → Projects → Real Estate investment
https://drive.google.com/drive/folders/1p3jq_eiy1larrBiwkX9epBe3AQ7Gv5Hl

## Updating
Replace `index.html` (generated from `SGC_Investment_Hub.html` with the SEED
records emptied and `data-seed="blank"` on the `<html>` tag) and bump `CACHE` in
`sw.js` so installed devices pick up the new build.
