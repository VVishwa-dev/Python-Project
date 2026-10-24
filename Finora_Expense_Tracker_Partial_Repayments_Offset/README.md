# Finora — Personal Expense Tracker & Budget Alert

A polished Python + Streamlit student project for personal spending, savings goals, group funding, lending/borrowing, EMI tracking, charts and a data-aware money coach.

## Features
- Secure account registration and login (salted PBKDF2 password hashes).
- Local SQLite database for users, transactions, budgets, goals, group membership/contributions, debts and loans.
- Dashboard with monthly income, expenses, cash flow, spending breakdown and budget alert.
- Transaction journal with filters and full record details (date, creation timestamp, method, reference, notes and source/verification status).
- CSV transaction import, preview and manual review.
- Savings goals with progress meter and target-date daily savings estimate.
- Group saving goals, member contributions, contribution chart and rough time-to-goal estimate based on recent recorded contributions.
- Lending/borrowing ledger with due dates and returned/settled status.
- Loan and EMI planner.
- Rule-based money coach that uses the current user's saved tracker data.
- Plotly charts, custom SVG illustrations and premium CSS styling.

## Run locally
1. Install Python 3.10+.
2. Unzip this project and open a terminal in the `Finora_Expense_Tracker` folder.
3. Create a virtual environment (recommended):
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows: `py -m venv .venv && .venv\\Scripts\\activate`
4. Install packages: `pip install -r requirements.txt`
5. Start app: `streamlit run app.py`
6. Open the local URL shown by Streamlit (usually http://localhost:8501).
7. Register a user. Your local database file `finora.db` is created automatically.

## CSV import format
Required headers: `date,description,amount,type`
Optional: `category,reference,payment_method`
Use ISO dates like `2026-10-21`. Type must be `Income` or `Expense`. Amounts should be positive; type determines the direction.

## Important integration limits
This is a learning prototype, not a live banking or payment app:
- It cannot automatically read every transaction from a phone or bank by itself.
- CSV imports work for bank/UPI statements exported by the user.
- Real bank sync requires an authorised provider / account-aggregator or Open Banking API, explicit consent, security review and provider credentials.
- Actual UPI/QR payments require a bank or regulated payment provider. This app records contribution claims; it does not move money.
- Uploaded screenshots are not reliably verifiable proof of payment. A production version needs payment-provider callbacks and reconciliation.
- Group contribution records are not held in escrow and are not independently verified.
- Chatbot is a local rule-based assistant, not a general LLM. It can summarise tracker data and offer basic saving suggestions.

## Suggested next upgrades
1. Add automated tests and migrations.
2. Add transaction duplicate detection and CSV column mapping.
3. Add receipt OCR with explicit confirmation and no automatic "verified" label.
4. Add a consent-based banking provider integration; never ask users for online-banking passwords.
5. Add a payment gateway webhook and reconciliation flow for real payments.
6. Add secure deployment, HTTPS, CSRF protections, secrets management, encrypted backups, access controls and professional security testing.
7. Add an LLM provider only through server-side environment variables, with clear privacy disclosures and a no-data-sharing mode.
8. Add optional notifications through a user-consented push/email service.

## Privacy notes
Keep `finora.db` private and back it up securely. This prototype is intended for local educational use. Do not deploy it publicly with real financial data before a security review.


## UI enhancements in this update
- Compact icon-first navigation bar with selected section label; responsive layout adjustments for small screens.
- Four user-selectable theme packs: Lavender Glass, Midnight Luxe, Mint Wealth, and Warm Sand. Theme choice is stored per user in SQLite for this local prototype.
- Category emoji/icon labels, including petrol/fuel, food, transport, shopping, bills, education and health.
- Personal income-versus-expenses bar chart plus existing category pie chart.
- Group contribution bar and pie charts.
- Securely random invitation tokens with 7-day expiry and revocation controls. For hosted use, set `app_url` in Streamlit Secrets. The invite flow currently uses the existing SQLite schema and is a prototype; do not expose it to the public until authentication, token redemption, and group access are reviewed.

## Important hosting / PWA status
This update improves the existing Streamlit prototype. It does **not** complete the PostgreSQL migration or production authentication. `database.py` still uses SQLite. Do not point it at PostgreSQL by merely adding a connection URL; all database operations and authentication must be migrated together, and row-level/group authorization policies must be tested.
The `pwa/` folder contains starter manifest/service-worker files but they are not wired into Streamlit. A proper installable PWA needs a top-level frontend or reverse proxy to serve manifest, icons and service worker at the app origin root. The current app can still be opened on phones as a responsive website.
