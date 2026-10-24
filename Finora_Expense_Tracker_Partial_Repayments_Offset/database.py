import sqlite3, os
from datetime import datetime
DB_PATH=os.environ.get("FINORA_DB_PATH","finora.db")
def conn():
    c=sqlite3.connect(DB_PATH,timeout=15); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, username TEXT UNIQUE NOT NULL, email TEXT, password_hash TEXT NOT NULL, salt TEXT NOT NULL, currency TEXT DEFAULT 'INR (₹)', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), type TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, txn_date TEXT NOT NULL, payment_method TEXT, reference TEXT, notes TEXT, verification_status TEXT, created_at TEXT NOT NULL, payment_time TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS budgets(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),month TEXT NOT NULL,amount REAL NOT NULL,UNIQUE(user_id,month));
        CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),name TEXT NOT NULL,target_amount REAL NOT NULL,saved_amount REAL NOT NULL,target_date TEXT,priority TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS goal_contributions(id INTEGER PRIMARY KEY,goal_id INTEGER NOT NULL REFERENCES goals(id),user_id INTEGER NOT NULL REFERENCES users(id),amount REAL NOT NULL,note TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS groups_funds(id INTEGER PRIMARY KEY,name TEXT NOT NULL,target_amount REAL NOT NULL,description TEXT,creator_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS group_members(id INTEGER PRIMARY KEY,group_id INTEGER NOT NULL REFERENCES groups_funds(id),user_id INTEGER NOT NULL REFERENCES users(id),joined_at TEXT NOT NULL,UNIQUE(group_id,user_id));
        CREATE TABLE IF NOT EXISTS group_contributions(id INTEGER PRIMARY KEY,group_id INTEGER NOT NULL REFERENCES groups_funds(id),user_id INTEGER NOT NULL REFERENCES users(id),amount REAL NOT NULL,reference TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS debts(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),direction TEXT NOT NULL,person TEXT NOT NULL,amount REAL NOT NULL,purpose TEXT,txn_date TEXT,due_date TEXT,status TEXT DEFAULT 'Pending',created_at TEXT NOT NULL,contact_number TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS debt_adjustments(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),debt_id INTEGER NOT NULL REFERENCES debts(id),related_debt_id INTEGER REFERENCES debts(id),adjustment_type TEXT NOT NULL CHECK(adjustment_type IN ('repayment','offset')),amount REAL NOT NULL CHECK(amount>0),note TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), entity_type TEXT NOT NULL, entity_id INTEGER, action TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS transaction_proofs(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), transaction_id INTEGER REFERENCES transactions(id) ON DELETE CASCADE, file_name TEXT NOT NULL, mime_type TEXT NOT NULL, file_data BLOB NOT NULL, extracted_text TEXT, review_status TEXT NOT NULL DEFAULT 'Needs manual review', created_at TEXT NOT NULL, entity_type TEXT DEFAULT 'transaction', entity_id INTEGER);
        CREATE TABLE IF NOT EXISTS loans(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),name TEXT NOT NULL,principal REAL NOT NULL,emi REAL NOT NULL,annual_rate REAL NOT NULL,next_due TEXT,remaining_months INTEGER,status TEXT DEFAULT 'Due',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS user_settings(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, theme TEXT NOT NULL DEFAULT 'Lavender Glass');
        CREATE TABLE IF NOT EXISTS group_invites(id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL REFERENCES groups_funds(id) ON DELETE CASCADE, token TEXT UNIQUE NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id), expires_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
        """)
        # Backward-compatible migration for existing Finora databases.
        cols = [r[1] for r in c.execute("PRAGMA table_info(debts)").fetchall()]
        tx_cols = [r[1] for r in c.execute("PRAGMA table_info(transactions)").fetchall()]
        if "payment_time" not in tx_cols: c.execute("ALTER TABLE transactions ADD COLUMN payment_time TEXT DEFAULT ''")
        if "contact_number" not in cols:
            c.execute("ALTER TABLE debts ADD COLUMN contact_number TEXT DEFAULT ''")
        proof_cols = [r[1] for r in c.execute("PRAGMA table_info(transaction_proofs)").fetchall()]
        if "entity_type" not in proof_cols: c.execute("ALTER TABLE transaction_proofs ADD COLUMN entity_type TEXT DEFAULT 'transaction'")
        if "entity_id" not in proof_cols: c.execute("ALTER TABLE transaction_proofs ADD COLUMN entity_id INTEGER")
def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def rows(sql,args=()):
    with conn() as c: return [dict(x) for x in c.execute(sql,args).fetchall()]
def log_audit(uid, entity_type, entity_id, action, details=""):
    with conn() as c:
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,entity_type,entity_id,action,details,now()))
def list_audit_logs(uid, limit=500):
    return rows("SELECT * FROM audit_logs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",(uid,limit))
def add_transaction(uid,typ,amount,category,desc,dt,method,ref="",notes="",verification="Manually added",payment_time=""):
    with conn() as c:
        cur=c.execute("INSERT INTO transactions(user_id,type,amount,category,description,txn_date,payment_method,reference,notes,verification_status,created_at,payment_time) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(uid,typ,float(amount),category,desc,dt,method,ref,notes,verification,now(),payment_time))
        tid=cur.lastrowid
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"transaction",tid,"created",f"{typ}: {desc}; amount={float(amount):.2f}; category={category}; date={dt}; payment_time={payment_time}; method={method}; reference={ref}; status={verification}",now()))
        return tid
def attach_transaction_proof(uid, transaction_id, file_name, mime_type, file_data, extracted_text="", entity_type="transaction", entity_id=None):
    if entity_id is None: entity_id = transaction_id
    with conn() as c:
        cur=c.execute("INSERT INTO transaction_proofs(user_id,transaction_id,file_name,mime_type,file_data,extracted_text,review_status,created_at,entity_type,entity_id) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,transaction_id if entity_type=="transaction" else None,file_name,mime_type,file_data,extracted_text,"Needs manual review",now(),entity_type,entity_id))
        if entity_type=="transaction": c.execute("UPDATE transactions SET verification_status=? WHERE id=? AND user_id=?",("Proof uploaded — needs manual review",transaction_id,uid))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,entity_type,entity_id,"proof uploaded",f"{file_name}; pending manual/provider verification; proof id={cur.lastrowid}",now()))
def get_proof_image(uid, proof_id):
    with conn() as c:
        r=c.execute("SELECT file_name,mime_type,file_data,extracted_text,review_status FROM transaction_proofs WHERE user_id=? AND id=?",(uid,proof_id)).fetchone()
        return dict(r) if r else None
def list_transaction_proofs(uid, transaction_id=None):
    sql="SELECT id,transaction_id,entity_type,entity_id,file_name,mime_type,extracted_text,review_status,created_at FROM transaction_proofs WHERE user_id=?"; args=[uid]
    if transaction_id is not None: sql += " AND transaction_id=?"; args.append(transaction_id)
    sql += " ORDER BY created_at DESC"
    return rows(sql,args)
def list_transactions(uid,start_date=None,end_date=None,txn_type=None,limit=100):
    sql="SELECT * FROM transactions WHERE user_id=?"; args=[uid]
    if start_date: sql+=" AND txn_date>=?"; args.append(start_date)
    if end_date: sql+=" AND txn_date<=?"; args.append(end_date)
    if txn_type: sql+=" AND type=?"; args.append(txn_type)
    sql+=" ORDER BY txn_date DESC, created_at DESC LIMIT ?"; args.append(limit)
    return rows(sql,args)
def delete_transaction(uid,tid):
    with conn() as c: c.execute("DELETE FROM transactions WHERE user_id=? AND id=?",(uid,tid))
def get_categories(typ):
    return ["Food & drinks","Transport","Petrol / fuel","Education","Shopping","Bills & utilities","Health","Entertainment","Rent / housing","Travel","Subscriptions","Savings","Salary","Freelance","Gift","Other"] if typ=="Expense" else ["Salary","Allowance","Freelance","Business","Refund","Gift","Interest","Other income"]
def get_budget(uid,month):
    r=rows("SELECT amount FROM budgets WHERE user_id=? AND month=?",(uid,month)); return float(r[0]["amount"]) if r else 0.0
def set_budget(uid,month,amount):
    with conn() as c: c.execute("INSERT INTO budgets(user_id,month,amount) VALUES(?,?,?) ON CONFLICT(user_id,month) DO UPDATE SET amount=excluded.amount",(uid,month,float(amount)))
def create_goal(uid,name,target,initial,due,priority):
    with conn() as c:
        cur=c.execute("INSERT INTO goals(user_id,name,target_amount,saved_amount,target_date,priority,created_at) VALUES(?,?,?,?,?,?,?)",(uid,name,target,initial,due,priority,now()))
        if initial>0: c.execute("INSERT INTO goal_contributions(goal_id,user_id,amount,note,created_at) VALUES(?,?,?,?,?)",(cur.lastrowid,uid,initial,"Initial savings",now()))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"savings_goal",cur.lastrowid,"goal created",f"name={name}; target={target}; initial_saved={initial}; due={due}; priority={priority}",now()))
def list_goals(uid): return rows("SELECT * FROM goals WHERE user_id=? ORDER BY created_at DESC",(uid,))
def contribute_goal(uid,gid,amount,note):
    with conn() as c:
        c.execute("UPDATE goals SET saved_amount=saved_amount+? WHERE id=? AND user_id=?",(amount,gid,uid))
        c.execute("INSERT INTO goal_contributions(goal_id,user_id,amount,note,created_at) SELECT ?,?,?,?,? WHERE changes()>0",(gid,uid,amount,note,now()))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"savings_goal",gid,"contribution added",f"amount={amount}; note={note}",now()))
def goal_contributions(gid,uid): return rows("SELECT amount,note,created_at FROM goal_contributions WHERE goal_id=? AND user_id=? ORDER BY created_at DESC",(gid,uid))
def create_group(uid,name,target,desc):
    with conn() as c:
        cur=c.execute("INSERT INTO groups_funds(name,target_amount,description,creator_id,created_at) VALUES(?,?,?,?,?)",(name,target,desc,uid,now()))
        gid=cur.lastrowid; c.execute("INSERT INTO group_members(group_id,user_id,joined_at) VALUES(?,?,?)",(gid,uid,now()))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"group_fund",gid,"group created",f"name={name}; target={target}; description={desc}",now()))
def list_groups(uid):
    return rows("SELECT g.*,u.name creator_name FROM groups_funds g JOIN group_members m ON m.group_id=g.id JOIN users u ON u.id=g.creator_id WHERE m.user_id=? ORDER BY g.created_at DESC",(uid,))
def join_group(uid,gid):
    if not rows("SELECT id FROM groups_funds WHERE id=?",(gid,)): return False,"No group found with that ID."
    try:
        with conn() as c: c.execute("INSERT INTO group_members(group_id,user_id,joined_at) VALUES(?,?,?)",(gid,uid,now()))
        return True,"Joined group."
    except sqlite3.IntegrityError: return False,"You're already a member of that group."
def contribute_group(uid,gid,amount,ref):
    with conn() as c:
        if c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?",(gid,uid)).fetchone():
            c.execute("INSERT INTO group_contributions(group_id,user_id,amount,reference,created_at) VALUES(?,?,?,?,?)",(gid,uid,amount,ref,now()))
            c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"group_fund",gid,"contribution added",f"amount={amount}; reference={ref}",now()))
def group_contributions(gid,detailed=False):
    if detailed: return rows("SELECT gc.amount,gc.reference,gc.created_at,u.name member_name FROM group_contributions gc JOIN users u ON u.id=gc.user_id WHERE gc.group_id=? ORDER BY gc.created_at DESC",(gid,))
    return rows("SELECT u.name member_name,COALESCE(SUM(gc.amount),0) total,COUNT(gc.id) contribution_count FROM group_members gm JOIN users u ON u.id=gm.user_id LEFT JOIN group_contributions gc ON gc.group_id=gm.group_id AND gc.user_id=gm.user_id WHERE gm.group_id=? GROUP BY u.id,u.name ORDER BY total DESC",(gid,))
def add_debt(uid,direction,person,amount,purpose,txn_date,due_date,contact_number=""):
    with conn() as c:
        cur=c.execute("INSERT INTO debts(user_id,direction,person,amount,purpose,txn_date,due_date,status,created_at,contact_number) VALUES(?,?,?,?,?,?,?,'Pending',?,?)",(uid,direction,person,amount,purpose,txn_date,due_date,now(),contact_number))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"debt",cur.lastrowid,"created",f"{direction}; person={person}; amount={amount}; due={due_date}; contact={contact_number}",now()))
def list_debts(uid): return rows("SELECT * FROM debts WHERE user_id=? ORDER BY due_date",(uid,))
def update_debt(uid,did,status):
    with conn() as c:
        c.execute("UPDATE debts SET status=? WHERE user_id=? AND id=?",(status,uid,did))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"debt",did,"status changed",status,now()))
def debt_balance(uid, did):
    items=rows("SELECT d.amount,d.status,COALESCE(SUM(a.amount),0) adjusted FROM debts d LEFT JOIN debt_adjustments a ON a.debt_id=d.id WHERE d.user_id=? AND d.id=? GROUP BY d.id",(uid,did))
    if not items or items[0]["status"] == "Returned": return 0.0
    return max(0.0, round(float(items[0]["amount"])-float(items[0]["adjusted"]),2))

def debt_adjustments(uid, did):
    return rows("SELECT * FROM debt_adjustments WHERE user_id=? AND debt_id=? ORDER BY created_at DESC",(uid,did))

def add_debt_repayment(uid, did, amount, note=""):
    amount=round(float(amount),2)
    with conn() as c:
        debt=c.execute("SELECT amount,person,direction FROM debts WHERE id=? AND user_id=?",(did,uid)).fetchone()
        if not debt: return False,"Debt entry not found."
        adjusted=c.execute("SELECT COALESCE(SUM(amount),0) total FROM debt_adjustments WHERE user_id=? AND debt_id=?",(uid,did)).fetchone()["total"]
        remaining=round(float(debt["amount"])-float(adjusted),2)
        if amount<=0 or amount>remaining+0.001: return False,f"Enter an amount up to ₹{remaining:,.2f}."
        c.execute("INSERT INTO debt_adjustments(user_id,debt_id,adjustment_type,amount,note,created_at) VALUES(?,?,'repayment',?,?,?)",(uid,did,amount,note,now()))
        new_balance=round(remaining-amount,2)
        c.execute("UPDATE debts SET status=? WHERE id=? AND user_id=?",("Returned" if new_balance<=0.009 else "Partially returned",did,uid))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"debt",did,"partial repayment recorded",f"person={debt['person']}; direction={debt['direction']}; paid={amount:.2f}; remaining={new_balance:.2f}; note={note}",now()))
    return True,f"Repayment recorded. Remaining balance: ₹{new_balance:,.2f}."

def offset_mutual_debts(uid, debt_a, debt_b, amount=None, note="Mutual debt offset agreed by user"):
    with conn() as c:
        a=c.execute("SELECT * FROM debts WHERE id=? AND user_id=?",(debt_a,uid)).fetchone()
        b=c.execute("SELECT * FROM debts WHERE id=? AND user_id=?",(debt_b,uid)).fetchone()
        if not a or not b: return False,"One of the debt entries was not found."
        if a["id"]==b["id"]: return False,"Choose two different entries."
        if a["direction"]==b["direction"]: return False,"Choose one 'I lent money' entry and one 'I borrowed money' entry."
        if a["person"].strip().casefold()!=b["person"].strip().casefold(): return False,"The person names do not match. Check that these entries belong to the same person."
        adj=c.execute("SELECT debt_id,SUM(amount) total FROM debt_adjustments WHERE user_id=? AND debt_id IN (?,?) GROUP BY debt_id",(uid,debt_a,debt_b)).fetchall()
        sums={r["debt_id"]:float(r["total"]) for r in adj}
        bal_a=round(float(a["amount"])-sums.get(debt_a,0),2); bal_b=round(float(b["amount"])-sums.get(debt_b,0),2)
        max_offset=min(bal_a,bal_b)
        use_amount=round(float(amount if amount is not None else max_offset),2)
        if max_offset<=0 or use_amount<=0 or use_amount>max_offset+0.001: return False,f"Offset must be greater than ₹0 and no more than ₹{max_offset:,.2f}."
        for debt_id,other_id in ((debt_a,debt_b),(debt_b,debt_a)):
            c.execute("INSERT INTO debt_adjustments(user_id,debt_id,related_debt_id,adjustment_type,amount,note,created_at) VALUES(?,?,?,'offset',?,?,?)",(uid,debt_id,other_id,use_amount,note,now()))
        for d,bal in ((a,bal_a-use_amount),(b,bal_b-use_amount)):
            c.execute("UPDATE debts SET status=? WHERE id=? AND user_id=?",("Returned" if bal<=0.009 else "Partially returned",d["id"],uid))
        c.execute("INSERT INTO audit_logs(user_id,entity_type,entity_id,action,details,created_at) VALUES(?,?,?,?,?,?)",(uid,"debt_offset",debt_a,"mutual debts offset",f"same_person={a['person']}; debt_ids={debt_a},{debt_b}; offset={use_amount:.2f}; note={note}",now()))
    return True,f"Offset of ₹{use_amount:,.2f} recorded against both entries. Remaining balances: ₹{max(0,bal_a-use_amount):,.2f} and ₹{max(0,bal_b-use_amount):,.2f}."

def add_loan(uid,name,principal,emi,rate,due,months):
    with conn() as c: c.execute("INSERT INTO loans(user_id,name,principal,emi,annual_rate,next_due,remaining_months,created_at) VALUES(?,?,?,?,?,?,?,?)",(uid,name,principal,emi,rate,due,months,now()))
def list_loans(uid): return rows("SELECT * FROM loans WHERE user_id=? ORDER BY next_due",(uid,))
def update_loan(uid,lid,status):
    with conn() as c: c.execute("UPDATE loans SET status=? WHERE user_id=? AND id=?",(status,uid,lid))
def get_profile(uid):
    r=rows("SELECT name,email,currency FROM users WHERE id=?",(uid,)); return r[0] if r else {"name":"","email":"","currency":"INR (₹)"}
def save_profile(uid,name,email,currency):
    with conn() as c: c.execute("UPDATE users SET name=?,email=?,currency=? WHERE id=?",(name,email,currency,uid))
def get_summary(uid):
    return rows("SELECT type,SUM(amount) total FROM transactions WHERE user_id=? GROUP BY type",(uid,))


def get_theme(uid):
    r=rows("SELECT theme FROM user_settings WHERE user_id=?",(uid,))
    return r[0]["theme"] if r else "Lavender Glass"

def set_theme(uid, theme):
    with conn() as c:
        c.execute("INSERT INTO user_settings(user_id,theme) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET theme=excluded.theme",(uid,theme))

def create_group_invite(uid, gid, token, expires_at):
    with conn() as c:
        member=c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?",(gid,uid)).fetchone()
        if not member:
            return False
        c.execute("INSERT INTO group_invites(group_id,token,created_by,expires_at,active,created_at) VALUES(?,?,?,?,1,?)",(gid,token,uid,expires_at,now()))
        return True

def redeem_group_invite(uid, token):
    invite=rows("SELECT * FROM group_invites WHERE token=? AND active=1",(token,))
    if not invite:
        return False,"This invitation is invalid or has been revoked."
    inv=invite[0]
    if inv["expires_at"] < now():
        return False,"This invitation has expired. Ask a group member for a new link."
    return join_group(uid,int(inv["group_id"]))

def revoke_group_invite(uid, invite_id):
    with conn() as c:
        c.execute("UPDATE group_invites SET active=0 WHERE id=? AND created_by=?",(invite_id,uid))

def list_group_invites(uid, gid):
    return rows("SELECT id,token,expires_at,active,created_at FROM group_invites WHERE group_id=? AND created_by=? ORDER BY created_at DESC",(gid,uid))
