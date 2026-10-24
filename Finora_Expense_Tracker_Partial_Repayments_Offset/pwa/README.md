# PWA starter assets

The manifest and service worker are starter assets, not yet wired into Streamlit.
A full installable PWA needs these served from the app origin at `/manifest.webmanifest`,
`/service-worker.js`, and `/icons/...`, plus a `<link rel="manifest">` and service-worker
registration in the top-level page. Streamlit Community Cloud does not automatically
serve these files at the required root paths. For a reliable installable experience,
add a small React/Vite frontend (recommended) or a reverse proxy that serves these assets
at the origin root while forwarding app traffic to Streamlit.

Do not cache private financial pages or API responses in a service worker.
