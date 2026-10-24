import pandas as pd
def answer_question(question,context):
    q=question.lower()
    rows=context.get("transactions",[]) or []
    df=pd.DataFrame(rows)
    budget=float(context.get("budget",0) or 0)
    goals=context.get("goals",[]) or []
    debts=context.get("debts",[]) or []
    loans=context.get("loans",[]) or []
    if df.empty:
        return ("I don't have enough transaction history for personalised spending insights yet. Add or import a few transactions first. Then I can identify your largest categories, compare spending with your budget, and suggest realistic reductions. Start with small changes rather than cutting essentials.")
    exp=df[df.type=="Expense"] if "type" in df else pd.DataFrame()
    inc=df[df.type=="Income"] if "type" in df else pd.DataFrame()
    total=float(exp.amount.sum()) if not exp.empty else 0
    income=float(inc.amount.sum()) if not inc.empty else 0
    cats=exp.groupby("category").amount.sum().sort_values(ascending=False) if not exp.empty else pd.Series(dtype=float)
    top=cats.head(3)
    if any(x in q for x in ["where","spend","spending","category","most"]):
        if top.empty: return f"You have recorded {income:.2f} in income and no expenses in this period. Add expense records to see categories."
        return "Your largest recorded spending categories are:\n\n"+"\n".join([f"- **{k}: ₹{v:,.2f}** ({v/max(total,1)*100:.1f}% of recorded expenses)" for k,v in top.items()])+f"\n\nTotal recorded expenses: **₹{total:,.2f}**. Review recurring subscriptions, food delivery, impulse shopping and transport choices where relevant—but protect essentials and wellbeing."
    if any(x in q for x in ["save","reduce","cut","less","budget"]):
        suggestions=[]
        for k,v in top.items():
            if any(t in k.lower() for t in ["food","entertainment","shopping","subscription","travel","transport"]):
                suggestions.append((k,float(v)*.10))
        if not suggestions and not top.empty: suggestions=[(k,float(v)*.05) for k,v in top.head(2).items()]
        potential=sum(v for _,v in suggestions)
        lines=[f"- Try a **10% review target** for **{k}**: about ₹{v:,.0f} per month, if realistic." for k,v in suggestions]
        if not lines: lines=["- Set a small weekly discretionary limit and record every purchase for two weeks."]
        lines.append("- Automate a small transfer to a goal after income arrives, if your account balance and bills allow.")
        lines.append("- Check for unused subscriptions and compare planned purchases after a 24-hour pause.")
        budget_note = ""
        if budget:
            if total > budget:
                budget_note = f" Your monthly budget is ₹{budget:,.2f}; you are over by ₹{total-budget:,.2f}."
            else:
                budget_note = f" Your monthly budget is ₹{budget:,.2f}; you have ₹{budget-total:,.2f} of budget remaining."
        else:
            budget_note = " You have not set a monthly budget yet."
        return f"Based on your recorded data, expenses are **₹{total:,.2f}** and income is **₹{income:,.2f}** for the selected period." + budget_note + "\\n\\n**A realistic starting plan**\\n" + "\\n".join(lines) + f"\\n\\nPotential review amount from these category targets: around **₹{potential:,.0f}**. This is a planning estimate, not a guarantee. Do not cut necessary food, health, education, rent or minimum debt payments."
    if any(x in q for x in ["goal","saving meter","target","achieve","days"]):
        if not goals: return "You haven't created a savings goal yet. Add one under **Savings goals** with a target and date. I'll then show the remaining amount and daily pace needed."
        lines=[]
        for g in goals:
            gap=max(float(g["target_amount"])-float(g["saved_amount"]),0)
            days=max((pd.to_datetime(g["target_date"]).date()-pd.Timestamp.today().date()).days,1) if g.get("target_date") else None
            lines.append(f"- **{g['name']}**: {float(g['saved_amount'])/max(float(g['target_amount']),1)*100:.1f}% complete; ₹{gap:,.2f} remaining"+(f"; about ₹{gap/days:,.0f}/day to reach the target date." if days else "."))
        return "Your current goal meters:\n\n"+"\n".join(lines)
    if any(x in q for x in ["loan","emi","debt","borrow","lend","owe"]):
        return f"You have **{len(loans)} tracked loan(s)** and **{len(debts)} lending/borrowing record(s)**. Monthly EMI commitments total ₹{sum(float(x['emi']) for x in loans):,.2f}. Review upcoming due dates, keep minimum payments current, and contact your lender if you anticipate missing a payment. Tracker status is not confirmation from a lender."
    if any(x in q for x in ["income","cash flow","left","balance","net"]):
        return f"For the records in this period: **income ₹{income:,.2f}**, **expenses ₹{total:,.2f}**, and **cash flow ₹{income-total:,.2f}**. This is based only on transactions entered or imported here, not your live bank balance."
    return f"Here's what I can see in your tracker: income **₹{income:,.2f}**, expenses **₹{total:,.2f}**, and cash flow **₹{income-total:,.2f}**. I can help with spending categories, budget alerts, saving goals, group contributions, lending/borrowing and EMI tracking. Try asking “What can I reduce to save more?”"
