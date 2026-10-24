# Finora Expense Tracker — Feature & Code Guide

## What this version adds

- WhatsApp-inspired fixed bottom navigation and four theme packs.
- Lend/borrow contact phone field and due-date alerts inside the app.
- A WhatsApp link that opens a pre-filled reminder message for the contact. You review and press **Send** in WhatsApp.
- Payment time, transaction date, payment method, UTR/reference, notes and recorded timestamp for income/expenses.
- Optional screenshot evidence for income/expenses, savings-goal contributions and group-fund contributions.
- Optional OCR text extraction for transaction screenshots when Pillow, `pytesseract`, and the Tesseract system program are installed.
- Audit log rows for transaction creation, proof uploads, debt creation/status updates, savings-goal creation/contributions and group-fund creation/contributions.
- SQLite migrations to add the new fields to an existing local database without deleting its records.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit (usually `http://localhost:8501`). Stop the server with `Ctrl+C`.

### Optional screenshot OCR setup

OCR is optional. Install Python packages with `pip install pillow pytesseract` and install the Tesseract OCR system binary for your operating system. If Tesseract is unavailable, the app still stores proof images but OCR text extraction will not work. Do not install OCR packages if you do not need this feature.

## Files and what each one does

- `app.py` — Streamlit user interface, page routing, forms, theme CSS, due-date notices, proof upload, OCR text extraction and display.
- `database.py` — SQLite tables and database functions. It stores user accounts, transactions, budgets, savings goals, group funds, debts, loans, proof images and audit events.
- `auth.py` — registration/login helpers and password hashing. Passwords should never be stored in plain text.
- `assistant.py` — rule-based/AI-style money-coach response logic using the financial context supplied by the app.
- `visuals.py` — SVG illustrations used in the interface.
- `pwa/` — progressive web app manifest/service-worker assets for installability/offline shell experiments; these do not provide native SMS or bank access.
- `requirements.txt` — Python package dependencies.
- `finora.db` — local SQLite database created when the app runs (kept on the computer running Streamlit; do not share it publicly).
- `sample_transactions.csv` — example CSV data for import testing.

## Important concepts used

- **Python**: application logic, validation, date handling and message templates.
- **Streamlit**: forms, pages, navigation, buttons, upload widgets, alerts, tables and metrics.
- **SQLite / `sqlite3`**: local relational database. SQL tables link records to a user ID and use parameterized queries.
- **Pandas**: turns transaction/history records into dataframes for tables and analysis.
- **Plotly Express**: charts for spending and group contributions.
- **CSS inside `st.markdown`**: themes, responsive spacing, cards and the fixed bottom navigation appearance.
- **`st.session_state`**: holds the currently logged-in user and selected page during reruns.
- **`datetime` / `date`**: stores record timestamps and compares due dates.
- **URL encoding (`urllib.parse.quote`)**: safely places reminder text into a WhatsApp click-to-chat link.
- **OCR (optional)**: converts visible text from an uploaded screenshot to text for a human review. OCR is not a bank verification service.
- **Audit log**: append-only event records describing important user actions, with event time, entity, action and details.

## How to use the proof workflow

1. Add an income or expense in **Transactions**, or add a contribution in **Savings goals** / **Group funding**.
2. Enter the date, time, amount and UTR/reference exactly as shown by the bank/UPI receipt where available.
3. Upload a screenshot if you have one. The image is stored in the local SQLite database.
4. For transaction screenshots, optional OCR extracts visible text and gives rough “found/not detected” clues for amount/date/time/reference.
5. Open the **Proof uploads & audit log** expander in Transaction history to see proof metadata, preview stored screenshots and read OCR notes/audit events.
6. Independently open the bank/UPI app and verify payment status and UTR before relying on the record.

**Never label a transaction “verified” based only on a screenshot or OCR match.** Screenshots can be edited, text can be misread, and a screenshot does not prove that money settled. Strong verification requires an authorised payment/bank provider, verified server-side transaction status and reconciliation by UTR/reference. This project does not connect to UPI/bank APIs or move money.

## Due-date reminders and messaging limitation

Add the person's name, phone number with country code, amount, purpose and due date in **Lend & borrow**. When you open the app on or after the due date, Finora shows an in-app reminder. Use **Prepare WhatsApp reminder** to open WhatsApp with a pre-filled message. You must review and send it yourself.

The app does **not** silently or automatically send WhatsApp/SMS messages, and it cannot guarantee a notification while it is closed. Automatic outbound messaging requires a deployed background scheduler and an authorised provider/API (such as WhatsApp Business Platform or an SMS gateway), recipient consent, credentials/secrets, delivery/error handling and compliance with provider rules. Native phone notifications also require a suitable mobile app/browser permission and service-worker support.

## Audit log coverage

The audit log records important actions that are implemented in this version, including transaction creation (income/expense), evidence upload, debt creation/status change, savings-goal creation/contributions and group-fund creation/contributions. It is an application history, not a tamper-proof financial ledger: someone with direct access to the SQLite database can alter it. Back up the database and restrict file access.

## Security and privacy notes

- Proof images and finance records are stored locally in `finora.db`. Screenshots may contain names, account details or UTRs; upload only what you need and protect the computer/database.
- A screenshot is stored as evidence; do not upload someone else's private details without permission.
- Do not publish `finora.db`, `.env`, secrets or credentials to GitHub.
- For production use, add HTTPS, encrypted backups, access controls, secure file retention/deletion, server-side audit protections, tests, monitoring and a privacy notice.
- This educational prototype is not a bank, payment processor or legal/accounting service.
