import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from urllib.parse import quote
from database import init_db, add_transaction, list_transactions, delete_transaction, get_summary, get_categories, create_goal, list_goals, contribute_goal, goal_contributions, create_group, list_groups, join_group, contribute_group, group_contributions, add_debt, list_debts, update_debt, debt_balance, debt_adjustments, add_debt_repayment, offset_mutual_debts, add_loan, list_loans, update_loan, get_budget, set_budget, get_profile, save_profile, get_theme, set_theme, create_group_invite, redeem_group_invite, list_group_invites, revoke_group_invite, attach_transaction_proof, list_transaction_proofs, list_audit_logs, get_proof_image
from auth import register_user, login_user
from assistant import answer_question
from visuals import HERO_SVG, EMPTY_SVG

st.set_page_config(page_title="Finora · Personal Finance", page_icon="💠", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--ink:#172033;--muted:#7b8498;--purple:#6757e8;--mint:#b9f3dc;--line:#e9ebf3;}
html,body,[class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:linear-gradient(135deg,#f7f8ff 0%,#f7fbfa 52%,#fbf8ff 100%);color:var(--ink);}
.block-container {padding-top:1.6rem;max-width:1440px;}
h1,h2,h3 {font-family:'Manrope',sans-serif;letter-spacing:-.035em;color:#172033;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#171c35,#29264d);color:white;}
[data-testid="stSidebar"] * {color:#f4f3ff!important;}
[data-testid="stMetric"] {background:white;border:1px solid #eceef6;padding:18px 20px;border-radius:18px;box-shadow:0 7px 24px #22234a08;}
div[data-testid="stForm"] {background:white;padding:18px;border:1px solid var(--line);border-radius:18px;}
.stButton>button {border-radius:12px;border:0;background:#6757e8;color:white;font-weight:700;padding:.55rem 1rem;}
.stButton>button:hover {background:#5142cb;color:white;box-shadow:0 8px 22px #6757e833;}
.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"],.stDateInput input,.stTextArea textarea {border-radius:11px!important;}
.hero {background:linear-gradient(115deg,#201d46,#5446b7 62%,#897cf0);border-radius:28px;padding:28px 32px;color:white;display:flex;gap:24px;align-items:center;box-shadow:0 18px 50px #43369a25;margin-bottom:18px;}
.hero h1 {color:white;font-size:2.2rem;margin:0 0 8px 0;}
.hero p {color:#e4e1ff;margin:0;max-width:620px;}
.pill {display:inline-block;background:#ffffff20;border:1px solid #ffffff35;padding:6px 12px;border-radius:30px;font-size:.8rem;margin-bottom:12px;}
.panel {background:white;border:1px solid #eceef6;border-radius:20px;padding:20px 22px;box-shadow:0 8px 30px #20204a05;margin-bottom:14px;}
.muted {color:#7b8498;font-size:.92rem;}
.smallcaps {font-size:.75rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:#8b91a7;}
.tip {background:#edfbf5;border-left:4px solid #40bd91;padding:14px 16px;border-radius:12px;color:#285747;}
.stProgress > div > div {background:linear-gradient(90deg,#6557e8,#46c9a0);}
div[data-testid="stDataFrame"] {border-radius:15px;overflow:hidden;}
/* WhatsApp-inspired fixed bottom navigation. */
div[role="radiogroup"][aria-label="Finora navigation"] {position:fixed;left:50%;transform:translateX(-50%);bottom:12px;z-index:9999;display:flex;justify-content:space-around;gap:4px;width:min(760px,calc(100vw - 28px));background:rgba(255,255,255,.96);backdrop-filter:blur(18px);padding:8px 10px;border:1px solid #e5e8f0;border-radius:24px;box-shadow:0 12px 40px #20204a22;}
div[role="radiogroup"][aria-label="Finora navigation"] label {flex:1;min-width:0;padding:7px 5px;border-radius:15px;justify-content:center;align-items:center;transition:background .18s ease;}
div[role="radiogroup"][aria-label="Finora navigation"] label p {font-size:12px;font-weight:650;margin:2px 0 0;text-align:center;white-space:nowrap;}
div[role="radiogroup"][aria-label="Finora navigation"] label:has(input:checked) {background:#e9e7ff;color:#5d4bdc;}
div[role="radiogroup"][aria-label="Finora navigation"] label:has(input:checked) p {color:#5d4bdc;font-weight:800;}
[data-testid="stAppViewContainer"] .main .block-container {padding-bottom:7rem;}
@media(max-width:700px){.block-container{padding-top:.6rem;padding-bottom:8rem!important;padding-left:.7rem;padding-right:.7rem;} h1{font-size:1.55rem!important;} [data-testid="stSidebar"]{min-width:0;} div[role="radiogroup"][aria-label="Finora navigation"]{bottom:8px;gap:1px;padding:6px;width:calc(100vw - 16px);} div[role="radiogroup"][aria-label="Finora navigation"] label{padding:7px 2px;} div[role="radiogroup"][aria-label="Finora navigation"] label p{font-size:10px;}}

</style>
""", unsafe_allow_html=True)

def money(v): return f"₹{float(v or 0):,.2f}"
CATEGORY_ICONS={
    "Food & drinks":"🍔","Transport":"🚌","Petrol":"⛽","Petrol / fuel":"⛽","Fuel":"⛽","Education":"📚",
    "Shopping":"🛍️","Bills & utilities":"💡","Health":"💊","Entertainment":"🎬",
    "Rent / housing":"🏠","Travel":"✈️","Subscriptions":"📱","Savings":"🎯",
    "Salary":"💼","Freelance":"💻","Gift":"🎁","Allowance":"💵",
    "Business":"🏪","Refund":"↩️","Interest":"📈","Other":"📦","Other income":"💰"
}
def category_label(value): return f"{CATEGORY_ICONS.get(value, '💳')}  {value}"
def header(title, subtitle):
    st.markdown(f"<div style='margin:6px 0 20px'><div class='smallcaps'>FINORA · YOUR MONEY, WITH CLARITY</div><h1 style='margin:3px 0'>{title}</h1><div class='muted'>{subtitle}</div></div>", unsafe_allow_html=True)

if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    left,right=st.columns([1.15,1],gap="large")
    with left:
        st.markdown(HERO_SVG, unsafe_allow_html=True)
        st.markdown("<h1 style='font-size:2.6rem;margin:12px 0 4px'>Make your money<br>work with purpose.</h1><p class='muted'>A calmer, smarter space for spending, saving, shared goals and debt tracking.</p>",unsafe_allow_html=True)
        st.markdown("<div class='panel'><b>✦ Your complete money picture</b><br><span class='muted'>Spending insights · Goal meters · Group funds · Lending ledger · EMI planner · AI-style money coach</span></div>",unsafe_allow_html=True)
    with right:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        tab1,tab2=st.tabs(["Sign in","Create account"])
        with tab1:
            with st.form("login"):
                username=st.text_input("Username")
                password=st.text_input("Password",type="password")
                submit=st.form_submit_button("Sign in",use_container_width=True)
                if submit:
                    u=login_user(username,password)
                    if u: st.session_state.user=u; st.rerun()
                    else: st.error("Login failed. Check your username/password.")
        with tab2:
            with st.form("register"):
                name=st.text_input("Your name")
                username2=st.text_input("Choose username")
                email=st.text_input("Email (optional)")
                password2=st.text_input("Create password",type="password")
                confirm=st.text_input("Confirm password",type="password")
                submit2=st.form_submit_button("Create my secure space",use_container_width=True)
                if submit2:
                    if not name.strip() or not username2.strip() or len(password2)<8: st.error("Enter a name and username. Password must be at least 8 characters.")
                    elif password2!=confirm: st.error("Passwords do not match.")
                    else:
                        ok,msg=register_user(name.strip(),username2.strip(),email.strip(),password2)
                        if ok: st.success(msg+" You can sign in now.")
                        else: st.error(msg)
        st.caption("Demo note: data is stored in a local SQLite database on the computer running this app. Use your own device and protect your password.")
    st.stop()

user=st.session_state.get("user")
if not isinstance(user, dict) or user.get("id") is None:
    st.session_state.user = None
    st.rerun()
uid=user["id"]

# Apply a per-user theme. Fall back safely if a legacy database has an unknown value.
try:
    theme=get_theme(uid) or "Lavender Glass"
except (KeyError, TypeError, ValueError):
    theme="Lavender Glass"
theme_css={
    "Lavender Glass": ( "#f7f8ff", "#6757e8", "#ffffff", "#172033"),
    "Midnight Luxe": ("#151629", "#9a8cff", "#22243b", "#f4f4ff"),
    "Mint Wealth": ("#f0faf5", "#18865c", "#ffffff", "#16372b"),
    "Warm Sand": ("#fff8ef", "#b66b20", "#ffffff", "#352719"),
}
bg,accent,card,ink=theme_css.get(theme,theme_css["Lavender Glass"])
st.markdown(f"<style>:root{{--purple:{accent};}} .stApp{{background:{bg}!important;color:{ink}!important;}} h1,h2,h3,h4,p,label,[data-testid='stMarkdownContainer']{{color:{ink};}} [data-testid='stMetric'],div[data-testid='stForm'],.panel{{background:{card}!important;color:{ink}!important;border-color:{accent}22!important;}} [data-testid='stMetric'] label,[data-testid='stMetric'] [data-testid='stMetricValue']{{color:{ink}!important;}} .stButton>button{{background:{accent}!important;color:#fff!important;}} div[role='radiogroup'][aria-label='Finora navigation']{{background:{card}!important;border-color:{accent}33!important;}} div[role='radiogroup'][aria-label='Finora navigation'] label p{{color:{ink}!important;}} div[role='radiogroup'][aria-label='Finora navigation'] label:has(input:checked){{background:{accent}22!important;}} div[role='radiogroup'][aria-label='Finora navigation'] label:has(input:checked) p{{color:{accent}!important;}}</style>",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 💠 finora")
    st.caption("PERSONAL FINANCE STUDIO")
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.caption(f"{theme} theme")
    if st.button("Sign out",use_container_width=True):
        st.session_state.user=None; st.rerun()
    st.markdown("---")
    st.caption("Use the icon bar to navigate. Your personal records remain separate from group records.")

pages=["Overview","Transactions","Budgets & insights","Savings goals","Group funding","Lend & borrow","Loans & EMI","Money coach","Import & connections","Settings"]
nav_icons={"Overview":"⌂","Transactions":"▤","Budgets & insights":"▥","Savings goals":"◎","Group funding":"♧","Lend & borrow":"⇄","Loans & EMI":"▣","Money coach":"◌","Import & connections":"↗","Settings":"⚙"}
primary_pages=["Overview","Transactions","Budgets & insights","Savings goals"]
primary_labels={"Overview":"Home","Transactions":"Activity","Budgets & insights":"Insights","Savings goals":"Goals"}
if "page" not in st.session_state or st.session_state.page not in pages: st.session_state.page="Overview"
current_page=st.session_state.page
current_primary=current_page if current_page in primary_pages else "More"
primary_options=primary_pages+["More"]
selected_primary=st.radio("Finora navigation",primary_options,index=primary_options.index(current_primary),horizontal=True,format_func=lambda p: f"{nav_icons.get(p,'••')}\n{primary_labels.get(p,'More')}",label_visibility="collapsed",key="nav_main_choice")
if selected_primary=="More":
    secondary_pages=pages[4:]
    if "nav_more_choice" not in st.session_state or st.session_state.nav_more_choice not in secondary_pages:
        st.session_state.nav_more_choice=current_page if current_page in secondary_pages else secondary_pages[0]
    selected=st.selectbox("More Finora tools",secondary_pages,index=secondary_pages.index(st.session_state.nav_more_choice),format_func=lambda p:f"{nav_icons[p]}  {p}",key="nav_more_choice")
else:
    selected=selected_primary
st.session_state.page=selected
page=selected
st.caption(f"{nav_icons[page]}  **{page}**")
# Due-date nudges are shown when the app is open. Sending messages is user-triggered via WhatsApp/SMS links.
try:
    pending_debts = [d for d in list_debts(uid) if d.get("due_date") and debt_balance(uid,d["id"]) > 0.009]
    due_now = [d for d in pending_debts if date.fromisoformat(d["due_date"]) <= date.today()]
    if due_now:
        with st.container(border=True):
            st.warning(f"🔔 You have {len(due_now)} lend/borrow item(s) due today or overdue.")
            for item in due_now[:3]:
                if item["direction"] == "I borrowed money":
                    msg=f"Hello {item['person']}, a friendly reminder that ₹{debt_balance(uid,item['id']):,.2f} remains for {item.get('purpose') or 'our previous transaction'}. The due date is {item['due_date']}. I will update you once it is settled."
                else:
                    msg=f"Hello {item['person']}, friendly reminder that ₹{debt_balance(uid,item['id']):,.2f} remains outstanding for {item.get('purpose') or 'our previous transaction'}, due {item['due_date']}. Please let me know when you can settle it. Thank you."
                st.write(f"**{item['person']}** · remaining ₹{debt_balance(uid,item['id']):,.2f} · due {item['due_date']}")
                phone="".join(ch for ch in (item.get("contact_number") or "") if ch.isdigit())
                if phone:
                    st.link_button("Open WhatsApp reminder", "https://wa.me/"+phone+"?text="+quote(msg), key=f"duewa{item['id']}")
                else:
                    st.caption("Add a contact number in Lend & borrow to open a pre-filled WhatsApp reminder.")
except (ValueError, TypeError):
    pass
# Redeem an invitation only after the visitor is authenticated.
try:
    invite_token=st.query_params.get("invite")
except Exception:
    invite_token=None
if invite_token and not st.session_state.get("invite_processed"):
    ok,msg=redeem_group_invite(uid,invite_token)
    st.session_state.invite_processed=True
    if ok: st.success("You've joined the savings group.")
    else: st.warning(msg)
    try: st.query_params.clear()
    except Exception: pass

if page=="Overview":
    header("Your financial snapshot", "A clear view of what came in, what went out, and what you're building.")
    st.markdown(f"<div class='hero'><div style='flex:1'><div class='pill'>✦ YOUR MONTH, AT A GLANCE</div><h1>Spend mindfully.<br>Save meaningfully.</h1><p>Build better money habits with practical insights, goal progress and a little more peace of mind.</p></div><div style='width:240px;max-width:30%'>{HERO_SVG}</div></div>",unsafe_allow_html=True)
    start=date.today().replace(day=1); end=date.today()
    tx=list_transactions(uid, start_date=str(start), end_date=str(end))
    df=pd.DataFrame(tx)
    inc=float(df[df.type=="Income"].amount.sum()) if not df.empty else 0
    exp=float(df[df.type=="Expense"].amount.sum()) if not df.empty else 0
    budget=get_budget(uid, str(start))
    goals=list_goals(uid)
    saved=sum(float(g["saved_amount"]) for g in goals)
    a,b,c,d=st.columns(4)
    a.metric("Income this month",money(inc),help="Income transactions recorded this month")
    b.metric("Spending this month",money(exp),delta=f"{(exp/budget*100):.0f}% of budget used" if budget else "Set a budget to track")
    c.metric("Cash flow",money(inc-exp),delta="Income − expenses")
    d.metric("Across savings goals",money(saved),delta=f"{len(goals)} active goals")
    col1,col2=st.columns([1.4,1],gap="large")
    with col1:
        st.markdown("<div class='panel'><h3>Spending rhythm</h3><div class='muted'>Your recorded transactions for the current month</div>",unsafe_allow_html=True)
        if not df.empty:
            expenses=df[df.type=="Expense"]
            if not expenses.empty:
                bycat=expenses.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
                st.plotly_chart(px.pie(bycat,names="category",values="amount",hole=.68,color_discrete_sequence=px.colors.qualitative.Pastel, title=""),use_container_width=True)
            else: st.info("No expenses recorded this month yet.")
        else: st.markdown(EMPTY_SVG,unsafe_allow_html=True); st.info("Add a transaction to bring your dashboard to life.")
        st.markdown("</div>",unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='panel'><h3>Budget pulse</h3><div class='muted'>Keep an eye on your monthly limit</div>",unsafe_allow_html=True)
        if budget:
            ratio=min(exp/budget,1)
            st.progress(ratio,text=f"{money(exp)} spent of {money(budget)}")
            if exp>=budget: st.error("You've reached or exceeded your budget. Pause and review non-essential spending.")
            elif ratio>=.8: st.warning("You're approaching your budget (80%+). Check flexible expenses.")
            else: st.success(f"{money(budget-exp)} remaining this month.")
        else: st.info("Set your monthly budget under Budgets & insights.")
        st.markdown("#### Active savings goals")
        for g in goals[:4]:
            ratio=min(float(g["saved_amount"])/max(float(g["target_amount"]),1),1)
            st.write(f"**{g['name']}** · {money(g['saved_amount'])} / {money(g['target_amount'])}")
            st.progress(ratio)
        if not goals: st.caption("Create a goal to see your savings meter here.")
        st.markdown("</div>",unsafe_allow_html=True)
    # Clear side-by-side income and expense comparison for the current month.
    if not df.empty:
        flow=df.groupby("type",as_index=False).amount.sum()
        st.markdown("### Income vs expenses")
        st.plotly_chart(px.bar(flow,x="type",y="amount",color="type",text_auto=".2s",title="This month's cash flow",color_discrete_map={"Income":"#35ae85","Expense":"#ef7890"}),use_container_width=True)
    st.markdown("<div class='panel'><h3>Latest activity</h3>",unsafe_allow_html=True)
    alltx=list_transactions(uid,limit=6)
    if alltx:
        for t in alltx:
            with st.expander(f"{'🟢' if t['type']=='Income' else '🟣'}  {t['description']}  ·  {money(t['amount'])}"):
                st.write(f"**Category:** {t['category']}  |  **Date:** {t['txn_date']}  |  **Time recorded:** {t['created_at']}")
                st.write(f"**Payment method:** {t['payment_method']}  |  **Reference:** {t['reference'] or 'Not provided'}")
                st.write(f"**Notes:** {t['notes'] or '—'}  |  **Verification:** {t['verification_status']}")
    else: st.caption("Your latest transactions will appear here.")
    st.markdown("</div>",unsafe_allow_html=True)

elif page=="Transactions":
    header("Transaction journal","Every transaction has a searchable record with amount, category, date, time, notes and reference.")
    tab1,tab2=st.tabs(["＋ Add transaction","Transaction history"])
    with tab1:
        with st.form("newtx",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            typ=c1.selectbox("Transaction type",["Expense","Income"])
            amount=c2.number_input("Amount (₹)",min_value=0.0,step=50.0)
            category=c3.selectbox("Category",get_categories(typ),format_func=category_label)
            c4,c5,c6=st.columns(3)
            desc=c4.text_input("Description",placeholder="e.g. Lunch at college")
            txn_date=c5.date_input("Transaction date",value=date.today())
            payment_time=st.time_input("Payment time (from bank/UPI receipt)",value=datetime.now().time().replace(second=0,microsecond=0))
            method=c6.selectbox("Payment method",["UPI","Cash","Debit card","Credit card","Bank transfer","Wallet","Other"])
            reference=st.text_input("Transaction/reference ID (optional)")
            notes=st.text_area("Notes (optional)",placeholder="Merchant, purpose, or extra details")
            proof=st.file_uploader("Payment proof screenshot (optional)",type=["png","jpg","jpeg"],key="transaction_proof")
            submitted=st.form_submit_button("Save transaction",use_container_width=True)
            if submitted:
                if amount<=0 or not desc.strip(): st.error("Enter a positive amount and a description.")
                else:
                    tid=add_transaction(uid,typ,amount,category,desc.strip(),str(txn_date),method,reference.strip(),notes.strip(),"Manually added",str(payment_time))
                    if proof is not None:
                        raw=proof.getvalue(); extracted=""
                        # Optional OCR: works only when Pillow, pytesseract and the Tesseract binary are installed.
                        try:
                            from PIL import Image
                            import pytesseract, io
                            extracted=pytesseract.image_to_string(Image.open(io.BytesIO(raw)))
                        except Exception:
                            extracted="OCR unavailable; please compare the screenshot manually."
                        attach_transaction_proof(uid,tid,proof.name,proof.type or "image/jpeg",raw,extracted)
                        if extracted and "OCR unavailable" not in extracted:
                            amt_text=f"{float(amount):.2f}"
                            st.info("Screenshot OCR text was extracted where possible. Amount/date/reference matching is only a review aid; confirm it against your bank/UPI app before treating the payment as verified.")
                            with st.expander("Review extracted screenshot text"):
                                st.code(extracted[:5000])
                                amount_digits=amt_text.replace(",","")
                                ocr_lower=extracted.lower()
                                amt_variants={f"{float(amount):.2f}",f"{float(amount):.0f}",f"{float(amount):,.2f}"}
                                amount_seen=any(v in extracted.replace(",", "") for v in amt_variants)
                                date_seen=str(txn_date) in extracted or txn_date.strftime("%d/%m/%Y") in extracted or txn_date.strftime("%d-%m-%Y") in extracted
                                time_seen=payment_time.strftime("%H:%M") in extracted or payment_time.strftime("%I:%M") in extracted
                                ref_seen=bool(reference.strip()) and reference.strip().lower() in ocr_lower
                                st.write(f"Entered amount: ₹{float(amount):,.2f} · Date: {txn_date} · Payment time: {payment_time} · UTR/reference: {reference or 'not entered'}")
                                st.write(f"OCR clues — amount text found: {'Yes' if amount_seen else 'Not detected'}; date text found: {'Yes' if date_seen else 'Not detected'}; time text found: {'Yes' if time_seen else 'Not detected'}; entered UTR text found: {'Yes' if ref_seen else 'Not detected / not entered'}.")
                                st.caption("These are approximate text matches only. OCR can miss or misread text, and even a matching screenshot does not prove settlement. Confirm the status and UTR in your bank/UPI app.")
                        st.warning("Proof saved as **Needs manual review**. An image alone cannot prove that funds settled; verify the payment in your bank/UPI app.")
                    st.success("Transaction saved to your journal and audit log."); st.rerun()
    with tab2:
        filt1,filt2,filt3=st.columns(3)
        typf=filt1.selectbox("Type filter",["All","Expense","Income"])
        fromd=filt2.date_input("From",value=date.today().replace(day=1),key="fromdate")
        tod=filt3.date_input("To",value=date.today(),key="todate")
        rows=list_transactions(uid, start_date=str(fromd),end_date=str(tod),txn_type=None if typf=="All" else typf,limit=1000)
        if rows:
            df=pd.DataFrame(rows)
            st.dataframe(df[["txn_date","payment_time","created_at","type","description","category","amount","payment_method","reference","verification_status"]],use_container_width=True,hide_index=True)
            st.markdown("#### Open a transaction for its full audit trail")
            options={f"{r['txn_date']} · {r['description']} · {money(r['amount'])} · ID {r['id']}":r for r in rows}
            chosen=st.selectbox("Select transaction",list(options))
            r=options[chosen]
            with st.container(border=True):
                x1,x2,x3=st.columns(3); x1.metric("Amount",money(r["amount"])); x2.metric("Type",r["type"]); x3.metric("Record ID",r["id"])
                st.write(f"**Description:** {r['description']}  \n**Category:** {r['category']}  \n**Transaction date:** {r['txn_date']}  \n**Payment time (entered):** {r.get('payment_time') or '—'}  \n**Recorded date/time:** {r['created_at']}  \n**Payment method:** {r['payment_method']}  \n**UTR / reference:** {r['reference'] or '—'}  \n**Notes:** {r['notes'] or '—'}  \n**Source / verification:** {r['verification_status']}")
                if st.checkbox("I understand deleting this record cannot be undone",key=f"confirmdel{r['id']}"):
                    if st.button("Delete selected transaction",key=f"del{r['id']}"): delete_transaction(uid,r["id"]); st.rerun()
        else: st.markdown(EMPTY_SVG,unsafe_allow_html=True); st.info("No transactions match those filters.")
        with st.expander("🧾 Proof uploads & audit log"):
            proofs=list_transaction_proofs(uid)
            if proofs:
                st.dataframe(pd.DataFrame(proofs),use_container_width=True,hide_index=True)
                proof_options={f"Proof {pr['id']} · {pr['entity_type']} · {pr['file_name']} · {pr['review_status']}":pr['id'] for pr in proofs}
                chosen_proof=st.selectbox("Preview stored proof",list(proof_options),key="proof_preview_choice")
                selected_proof=get_proof_image(uid,proof_options[chosen_proof])
                if selected_proof:
                    st.image(selected_proof["file_data"],caption=f"{selected_proof['file_name']} · {selected_proof['review_status']}",use_container_width=True)
                    if selected_proof.get("extracted_text"): 
                        with st.expander("OCR / review notes for this proof"): st.text(selected_proof["extracted_text"][:5000])
            else: st.caption("No proof screenshots uploaded yet.")
            logs=list_audit_logs(uid,limit=200)
            if logs: st.dataframe(pd.DataFrame(logs),use_container_width=True,hide_index=True)
            else: st.caption("Actions will appear here as you add records.")

elif page=="Budgets & insights":
    header("Budgets & insights","Understand your habits, compare categories, and catch budget drift before month-end.")
    month=date.today().replace(day=1); current=get_budget(uid,str(month))
    with st.form("budgetform"):
        newbudget=st.number_input("Monthly spending budget (₹)",min_value=0.0,value=float(current),step=500.0)
        if st.form_submit_button("Save monthly budget"):
            set_budget(uid,str(month),newbudget); st.success("Budget updated."); st.rerun()
    rows=list_transactions(uid,start_date=str(month),end_date=str(date.today()),txn_type="Expense")
    df=pd.DataFrame(rows)
    if not df.empty:
        spent=float(df.amount.sum()); remaining=newbudget-spent
        x,y,z=st.columns(3); x.metric("Monthly limit",money(newbudget)); y.metric("Spent",money(spent)); z.metric("Available",money(remaining),delta="Over budget" if remaining<0 else "Left to spend")
        st.progress(min(spent/max(newbudget,1),1),text=f"{spent/max(newbudget,1)*100:.0f}% of budget used")
        cat=df.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
        left,right=st.columns(2)
        with left: st.plotly_chart(px.bar(cat,x="category",y="amount",color="category",title="Spending by category",text_auto=".2s"),use_container_width=True)
        with right: st.plotly_chart(px.pie(cat,names="category",values="amount",hole=.55,title="Where your money goes"),use_container_width=True)
        st.markdown("#### Practical observations")
        top=cat.iloc[0]
        st.info(f"Your highest recorded expense category this month is **{top['category']}** at **{money(top['amount'])}**. Review whether any purchases here can be delayed, shared, or replaced with a lower-cost option.")
        if remaining<0: st.warning(f"You are {money(abs(remaining))} over your monthly budget. Prioritise essential bills and avoid treating credit as extra income.")
        elif newbudget and spent/newbudget>=.8: st.warning("You've used at least 80% of your budget. Consider setting a daily flexible-spending limit for the rest of the month.")
    else: st.info("Add a few expense transactions to unlock category charts and personalised observations.")

elif page=="Savings goals":
    header("Savings goals","Give every rupee a purpose. Track your target, progress, pace and estimated finish date.")
    with st.form("goalform",clear_on_submit=True):
        a,b=st.columns(2); name=a.text_input("Goal name",placeholder="Emergency fund / new laptop"); target=b.number_input("Target amount (₹)",min_value=1.0,step=500.0)
        c,d=st.columns(2); initial=c.number_input("Already saved (₹)",min_value=0.0,step=100.0); due=d.date_input("Target date (optional)",value=date.today()+timedelta(days=90))
        priority=st.selectbox("Priority",["Essential","High","Normal","Someday"])
        if st.form_submit_button("Create savings goal"):
            if name.strip(): create_goal(uid,name.strip(),target,initial,str(due),priority); st.success("Goal created."); st.rerun()
    goals=list_goals(uid)
    if not goals: st.markdown(EMPTY_SVG,unsafe_allow_html=True); st.info("Create your first savings goal above.")
    for g in goals:
        saved=float(g["saved_amount"]); target=float(g["target_amount"]); pct=min(saved/max(target,1),1); gap=max(target-saved,0)
        with st.container(border=True):
            a,b=st.columns([3,1]); a.subheader(g["name"]); b.metric("Progress",f"{pct*100:.1f}%")
            st.progress(pct,text=f"{money(saved)} saved of {money(target)}")
            x,y,z=st.columns(3); x.metric("Still needed",money(gap)); y.metric("Priority",g["priority"]); z.metric("Target date",g["target_date"] or "Not set")
            daily=gap/max((date.fromisoformat(g["target_date"])-date.today()).days,1) if g["target_date"] else 0
            if gap<=0: st.success("Goal achieved! Celebrate, then decide whether to maintain or redirect the habit.")
            elif g["target_date"]: st.caption(f"To reach your target by {g['target_date']}, aim to save about {money(daily)} per day from today.")
            with st.form(f"contribgoal{g['id']}"):
                amount=st.number_input("Add to this goal (₹)",min_value=0.0,step=100.0,key=f"gamount{g['id']}")
                note=st.text_input("Contribution note",key=f"gnote{g['id']}")
                proof_goal=st.file_uploader("Savings proof screenshot (optional)",type=["png","jpg","jpeg"],key=f"gproof{g['id']}")
                if st.form_submit_button("＋ Add savings"):
                    if amount>0:
                        contribute_goal(uid,g["id"],amount,note)
                        if proof_goal is not None:
                            from database import log_audit
                            attach_transaction_proof(uid,None,proof_goal.name,proof_goal.type or "image/jpeg",proof_goal.getvalue(),"OCR not run for savings proof",entity_type="savings_goal",entity_id=g["id"])
                        st.success("Contribution recorded in the savings history and audit log. Verify the transfer in your bank app."); st.rerun()
            history=goal_contributions(g["id"],uid)
            if history:
                with st.expander("Contribution history"):
                    st.dataframe(pd.DataFrame(history),use_container_width=True,hide_index=True)

elif page=="Group funding":
    header("Group funding","Save together for a trip, shared gift, event or team goal. Contributions are recorded per member.")
    tab1,tab2=st.tabs(["Create a group","Your groups"])
    with tab1:
        with st.form("groupcreate"):
            name=st.text_input("Group name",placeholder="Goa trip fund")
            target=st.number_input("Shared goal (₹)",min_value=1.0,step=500.0)
            desc=st.text_area("Purpose / group rules")
            if st.form_submit_button("Create group"):
                if name.strip(): create_group(uid,name.strip(),target,desc); st.success("Group created. Share the group ID with members so they can join."); st.rerun()
    with tab2:
        with st.form("joinform"):
            gid=st.number_input("Group ID to join",min_value=1,step=1)
            if st.form_submit_button("Join group"):
                ok,msg=join_group(uid,int(gid)); st.success(msg) if ok else st.error(msg)
        groups=list_groups(uid)
        if not groups: st.caption("Your groups will appear here.")
        for g in groups:
            members=group_contributions(g["id"]); total=sum(float(m["total"]) for m in members); target=float(g["target_amount"])
            with st.container(border=True):
                st.subheader(g["name"]); st.caption(f"Group ID: {g['id']} · Created by {g['creator_name']} · {g['description'] or 'No description'}")
                with st.expander("🔗 Invite friends with a link"):
                    st.caption("Invitation links expire after 7 days. Share only with people you trust.")
                    if st.button("Generate invitation link",key=f"makeinvite{g['id']}"):
                        token=secrets.token_urlsafe(32)
                        expiry=(datetime.now().astimezone()+timedelta(days=7)).isoformat(timespec="seconds")
                        if create_group_invite(uid,g["id"],token,expiry):
                            st.session_state[f"invite_link_{g['id']}"]=token
                    token=st.session_state.get(f"invite_link_{g['id']}")
                    if token:
                        try:
                            app_url=st.secrets.get("app_url","http://localhost:8501")
                        except Exception:
                            app_url="http://localhost:8501"
                        invite_url=f"{str(app_url).rstrip('/')}/?invite={token}"
                        st.code(invite_url,language=None)
                        st.link_button("Share invite via WhatsApp", "https://wa.me/?text="+__import__("urllib.parse",fromlist=["quote"]).quote("Join my Finora savings group: "+invite_url))
                        st.caption("For deployed use, set app_url in Streamlit Secrets to your public app URL.")
                    for inv in list_group_invites(uid,g["id"]):
                        if inv["active"]:
                            if st.button("Revoke invitation",key=f"revoke{inv['id']}"):
                                revoke_group_invite(uid,inv["id"])
                                if f"invite_link_{g['id']}" in st.session_state: del st.session_state[f"invite_link_{g['id']}"]
                                st.rerun()
                st.progress(min(total/max(target,1),1),text=f"{money(total)} contributed of {money(target)}")
                gap=max(target-total,0); st.write(f"**Remaining:** {money(gap)}")
                if gap<=0: st.success("Shared target reached!")
                else:
                    if total>0:
                        # Estimate pace from recorded contributions over the past 30 days.
                        hist=group_contributions(g["id"], detailed=True)
                        recent=sum(float(x["amount"]) for x in hist if x["created_at"][:10] >= str(date.today()-timedelta(days=30)))
                        if recent>0: st.caption(f"At the last 30-day contribution pace ({money(recent)}), estimated time to goal: about {max(1,int(gap/(recent/30)))} days.")
                st.markdown("**Contribution by member**")
                if members:
                    mdf=pd.DataFrame(members).rename(columns={"member_name":"Member","total":"Contributed","contribution_count":"Contributions"})
                    st.dataframe(mdf,use_container_width=True,hide_index=True)
                    st.plotly_chart(px.bar(mdf,x="Member",y="Contributed",color="Member",title="Group contribution breakdown",text_auto=".2s"),use_container_width=True)
                    if float(mdf["Contributed"].sum())>0:
                        st.plotly_chart(px.pie(mdf,names="Member",values="Contributed",hole=.55,title="Share of group contributions"),use_container_width=True)
                with st.form(f"groupcontrib{g['id']}"):
                    amount=st.number_input("Your contribution (₹)",min_value=0.0,step=100.0,key=f"gc{g['id']}")
                    ref=st.text_input("Payment reference / UTR (optional)",key=f"gr{g['id']}")
                    proof_group=st.file_uploader("Contribution proof screenshot (optional)",type=["png","jpg","jpeg"],key=f"gfproof{g['id']}")
                    if st.form_submit_button("Record contribution"):
                        if amount>0:
                            contribute_group(uid,g["id"],amount,ref)
                            if proof_group is not None:
                                from database import log_audit
                                attach_transaction_proof(uid,None,proof_group.name,proof_group.type or "image/jpeg",proof_group.getvalue(),"OCR not run for group contribution proof",entity_type="group_fund",entity_id=g["id"])
                            st.success("Contribution recorded in the group history and audit log. Verify the transfer in your bank app."); st.rerun()
                st.caption("Contribution records are not bank-verified. Confirm actual transfers separately before treating the group balance as money held in a real account.")

elif page=="Lend & borrow":
    header("Lend & borrow ledger","Track partial repayments and offset mutual balances only after you and the other person agree.")
    with st.form("debtform",clear_on_submit=True):
        a,b,c=st.columns(3); direction=a.selectbox("Record type",["I lent money","I borrowed money"]); person=b.text_input("Person's name"); amount=c.number_input("Original amount (₹)",min_value=1.0,step=100.0)
        d,e=st.columns(2); purpose=d.text_input("Purpose / bill details"); due=e.date_input("Due date",value=date.today()+timedelta(days=30))
        contact=st.text_input("Contact phone with country code (for example 9198XXXXXXXX)",help="Used to open a pre-filled WhatsApp reminder. Finora will not send messages automatically.")
        txn=st.date_input("Date of transaction",value=date.today(),key="debtdate")
        if st.form_submit_button("Add ledger entry"):
            if not person.strip(): st.error("Enter the person's name.")
            else:
                add_debt(uid,direction,person.strip(),amount,purpose,str(txn),str(due),contact.strip()); st.success("Ledger entry added."); st.rerun()

    debts=list_debts(uid)
    open_debts=[d for d in debts if debt_balance(uid,d["id"])>0.009]
    if open_debts:
        st.subheader("Settle mutual balances")
        st.caption("If you both owe each other money, select the two entries for the same person. Finora offsets only the amount you confirm, keeps both original entries, and logs the adjustment. No money is transferred by this action.")
        lent=[d for d in open_debts if d["direction"]=="I lent money"]
        borrowed=[d for d in open_debts if d["direction"]=="I borrowed money"]
        if lent and borrowed:
            with st.form("offset_form"):
                lent_choice=st.selectbox("They owe me",lent,format_func=lambda d:f"{d['person']} · original ₹{float(d['amount']):,.2f} · remaining ₹{debt_balance(uid,d['id']):,.2f} · #{d['id']}")
                borrow_choice=st.selectbox("I owe them",borrowed,format_func=lambda d:f"{d['person']} · original ₹{float(d['amount']):,.2f} · remaining ₹{debt_balance(uid,d['id']):,.2f} · #{d['id']}")
                max_off=min(debt_balance(uid,lent_choice["id"]),debt_balance(uid,borrow_choice["id"]))
                offset_amt=st.number_input("Amount to offset (₹)",min_value=0.01,max_value=float(max(0.01,max_off)),value=float(max_off),step=100.0)
                confirmed=st.checkbox("I confirmed with this person that these balances belong to the same person and we agree to offset this amount.")
                if st.form_submit_button("Review and record offset"):
                    if not confirmed: st.error("Please confirm agreement with the other person first.")
                    else:
                        ok,msg=offset_mutual_debts(uid,lent_choice["id"],borrow_choice["id"],offset_amt)
                        (st.success if ok else st.error)(msg)
                        if ok: st.rerun()
        else:
            st.info("Add at least one outstanding lent entry and one outstanding borrowed entry to use mutual offset.")

    st.subheader("Your entries")
    if debts:
        for d in debts:
            balance=debt_balance(uid,d["id"])
            with st.container(border=True):
                overdue=balance>0.009 and d["due_date"] and date.fromisoformat(d["due_date"])<date.today()
                st.write(f"### {d['direction']} · {d['person']}")
                x,y,z=st.columns(3); x.metric("Original amount",money(d["amount"])); y.metric("Remaining",money(balance)); z.metric("Due date",d["due_date"])
                st.caption(f"Status: {d['status']} · Purpose: {d['purpose'] or '—'} · Recorded: {d['txn_date']} · Contact: {d.get('contact_number') or 'not added'}")
                if overdue: st.error("Past the expected return date.")
                if balance>0.009:
                    repay_label="Record amount I paid back" if d["direction"]=="I borrowed money" else "Record amount they returned"
                    with st.form(f"repay_{d['id']}"):
                        paid=st.number_input(f"{repay_label} (₹)",min_value=0.01,max_value=float(balance),value=float(balance),step=100.0,key=f"repay_amt_{d['id']}")
                        note=st.text_input("Repayment note / UTR (optional)",key=f"repay_note_{d['id']}")
                        if st.form_submit_button("Save repayment"):
                            ok,msg=add_debt_repayment(uid,d["id"],paid,note)
                            (st.success if ok else st.error)(msg)
                            if ok: st.rerun()
                    if d["direction"] == "I borrowed money":
                        reminder=f"Hello {d['person']}, a friendly reminder that ₹{balance:,.2f} remains for {d.get('purpose') or 'our previous transaction'}. The due date was {d['due_date']}. I will update you once it is settled."
                    else:
                        reminder=f"Hello {d['person']}, friendly reminder that ₹{balance:,.2f} remains outstanding for {d.get('purpose') or 'our previous transaction'}, due {d['due_date']}. Please let me know when you can settle it. Thank you."
                    phone="".join(ch for ch in (d.get("contact_number") or "") if ch.isdigit())
                    if phone: st.link_button("💬 Prepare WhatsApp reminder for remaining balance", "https://wa.me/"+phone+"?text="+quote(reminder),key=f"debtwa{d['id']}")
                adjustments=debt_adjustments(uid,d["id"])
                if adjustments:
                    with st.expander("Repayment / offset history"):
                        for adj in adjustments:
                            st.write(f"• {adj['created_at'][:16]} — {adj['adjustment_type'].title()}: {money(adj['amount'])} · {adj.get('note') or 'No note'}")
    else: st.info("No lending or borrowing entries yet.")

elif page=="Loans & EMI":
    header("Loans & EMI planner","Keep repayment dates and monthly obligations visible so they don't surprise you.")
    with st.form("loanform",clear_on_submit=True):
        a,b=st.columns(2); lender=a.text_input("Lender / loan name"); principal=b.number_input("Outstanding principal (₹)",min_value=1.0,step=1000.0)
        c,d,e=st.columns(3); emi=c.number_input("Monthly EMI (₹)",min_value=1.0,step=100.0); rate=d.number_input("Annual interest rate (%)",min_value=0.0,max_value=60.0,step=.25); due=e.date_input("Next due date",value=date.today()+timedelta(days=7))
        term=st.number_input("Estimated remaining months",min_value=1,max_value=600,value=12)
        if st.form_submit_button("Add loan"):
            if lender.strip(): add_loan(uid,lender.strip(),principal,emi,rate,str(due),int(term)); st.success("Loan added."); st.rerun()
    loans=list_loans(uid)
    if loans:
        totalemi=sum(float(l["emi"]) for l in loans)
        st.metric("Total monthly EMI commitments",money(totalemi))
        st.plotly_chart(px.bar(pd.DataFrame(loans),x="name",y="emi",color="name",title="Monthly EMI by loan",text_auto=".2s"),use_container_width=True)
        for l in loans:
            with st.container(border=True):
                st.subheader(l["name"]); a,b,c=st.columns(3); a.metric("Outstanding",money(l["principal"])); b.metric("Monthly EMI",money(l["emi"])); c.metric("Next due",l["next_due"])
                monthly_rate=float(l["annual_rate"])/1200
                if monthly_rate>0:
                    interest=float(l["principal"])*monthly_rate
                    st.caption(f"Approximate interest portion of next EMI: {money(interest)} (estimate; actual lender schedule may differ).")
                if st.button("Mark next EMI as paid",key=f"paidemi{l['id']}"): update_loan(uid,l["id"],"Paid"); st.success("Marked as paid in your tracker. This does not make a bank payment."); st.rerun()
    else: st.info("Add your first loan to see EMI commitments.")

elif page=="Money coach":
    header("Your personal money coach","Ask practical questions. Answers use your saved tracker data and are educational, not professional financial advice.")
    month=date.today().replace(day=1)
    rows=list_transactions(uid,start_date=str(month),end_date=str(date.today()))
    df=pd.DataFrame(rows)
    if not df.empty:
        exp=df[df.type=="Expense"]; inc=df[df.type=="Income"]
        st.caption(f"Context loaded: {len(rows)} transactions this month · {money(exp.amount.sum())} spending · {money(inc.amount.sum())} income")
    else: st.caption("Add transactions for advice that reflects your actual spending.")
    prompt=st.chat_input("Ask: What can I reduce to save ₹2,000 more?")
    if "chat_history" not in st.session_state: st.session_state.chat_history=[]
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        context={"transactions":rows,"budget":get_budget(uid,str(month)),"goals":list_goals(uid),"debts":list_debts(uid),"loans":list_loans(uid)}
        response=answer_question(prompt,context)
        st.session_state.chat_history.append({"role":"assistant","content":response})
        with st.chat_message("assistant"): st.markdown(response)
    st.markdown("**Try asking**")
    c1,c2,c3=st.columns(3)
    if c1.button("Where am I spending most?"): st.session_state.chat_history.append({"role":"user","content":"Where am I spending most?"}); st.session_state.chat_history.append({"role":"assistant","content":answer_question("Where am I spending most?",{"transactions":rows,"budget":get_budget(uid,str(month)),"goals":list_goals(uid),"debts":list_debts(uid),"loans":list_loans(uid)})}); st.rerun()
    if c2.button("How can I save more?"): st.session_state.chat_history.append({"role":"user","content":"How can I save more?"}); st.session_state.chat_history.append({"role":"assistant","content":answer_question("How can I save more?",{"transactions":rows,"budget":get_budget(uid,str(month)),"goals":list_goals(uid),"debts":list_debts(uid),"loans":list_loans(uid)})}); st.rerun()
    if c3.button("Explain my budget"): st.session_state.chat_history.append({"role":"user","content":"Explain my budget"}); st.session_state.chat_history.append({"role":"assistant","content":answer_question("Explain my budget",{"transactions":rows,"budget":get_budget(uid,str(month)),"goals":list_goals(uid),"debts":list_debts(uid),"loans":list_loans(uid)})}); st.rerun()

elif page=="Import & connections":
    header("Import & connections","Bring in bank exports and receipts. Automatic bank feeds require a supported provider and explicit consent.")
    st.markdown("<div class='tip'><b>Privacy and safety first.</b> This student project does not collect bank passwords, read SMS messages, or connect directly to bank accounts. Use a CSV exported from your bank/UPI app. A future production version should use a regulated account-aggregator/Open Banking provider, read-only permissions, consent, encryption and revocation controls.</div>",unsafe_allow_html=True)
    st.markdown("### Import a transaction CSV")
    st.write("Expected columns: `date`, `description`, `amount`, `type` (Income/Expense), and optional `category`, `reference`, `payment_method`.")
    uploaded=st.file_uploader("Choose CSV file",type=["csv"])
    if uploaded:
        try:
            imp=pd.read_csv(uploaded); st.dataframe(imp.head(20),use_container_width=True)
            required={"date","description","amount","type"}
            if not required.issubset(set(imp.columns)): st.error("Missing required columns: "+", ".join(sorted(required-set(imp.columns))))
            else:
                if st.button("Import these rows"):
                    count=0
                    for _,r in imp.iterrows():
                        try:
                            typ=str(r["type"]).strip().title()
                            if typ not in ["Income","Expense"]: continue
                            dt=pd.to_datetime(r["date"]).date().isoformat()
                            amt=abs(float(r["amount"]))
                            if amt<=0: continue
                            desc=str(r["description"])
                            cat=str(r.get("category","Other"))
                            ref=str(r.get("reference","")) if pd.notna(r.get("reference","")) else ""
                            method=str(r.get("payment_method","Imported"))
                            add_transaction(uid,typ,amt,cat,desc,dt,method,ref,"Imported from CSV","Imported - not independently verified"); count+=1
                        except Exception: continue
                    st.success(f"Imported {count} rows. Please review duplicates and categories."); st.rerun()
        except Exception as e: st.error(f"Could not read CSV: {e}")
    st.markdown("### Proof verification notes")
    st.markdown("Upload a payment screenshot while adding an income or expense, or alongside a savings/group contribution. Finora stores the image locally and marks it **Needs manual review**. OCR is optional and only extracts visible text; it does not verify bank settlement.")
    st.markdown("### Future integrations roadmap")
    st.markdown("- **Mobile sync:** companion Android/iOS app with user permission, local processing and clear opt-out; OS and bank rules limit background transaction access.\n- **Bank feeds:** connect through an authorised provider/account aggregator; read-only access and explicit consent.\n- **UPI payments / QR:** actual payments must be handled by a bank/regulated payment provider. This app only records references; it does not move money.\n- **Transaction verification:** provider callback/webhook plus reconciliation; uploaded screenshots alone cannot reliably verify settlement.")

elif page=="Settings":
    header("Settings & profile","Manage your profile and understand how your data is stored.")
    profile=get_profile(uid)
    with st.form("profile"):
        name=st.text_input("Display name",value=profile["name"])
        email=st.text_input("Email",value=profile["email"] or "")
        currency=st.selectbox("Currency",["INR (₹)","USD ($)","EUR (€)","GBP (£)"],index=0)
        theme_options=["Lavender Glass","Midnight Luxe","Mint Wealth","Warm Sand"]
        saved_theme=get_theme(uid)
        chosen_theme=st.selectbox("Theme pack",theme_options,index=theme_options.index(saved_theme) if saved_theme in theme_options else 0)
        if st.form_submit_button("Save profile & theme"):
            save_profile(uid,name,email,currency); set_theme(uid,chosen_theme); st.success("Profile and theme saved."); st.rerun()
    st.markdown("### Data & security")
    st.markdown("- Passwords are stored as salted PBKDF2 hashes, not plain text.\n- Personal finance data lives in `finora.db` on the machine running Streamlit.\n- Do not deploy with sample/demo credentials or expose the database file publicly.\n- For a real multi-user hosted app, add HTTPS, encrypted backups, role-based access controls, rate limits, audit monitoring and a security review.")
    st.warning("This is an educational prototype, not a bank, payment processor, tax tool or investment adviser.")
