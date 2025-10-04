import streamlit as st
import os, csv, math, random
import pandas as pd
from datetime import datetime

OUTPUT_DIR = '/mnt/data/ai_virtual_factory'

# ---------- Helpers ----------
def write_markdown(fname, content):
    with open(os.path.join(OUTPUT_DIR, fname), 'w') as f:
        f.write(content)

# ---------- Autonomy Helpers (Sense → Think → Act) ----------
def _rand_trend(prev, lo, hi, step=0.1):
    val = prev + random.uniform(-step, step)
    return max(lo, min(hi, val))

def sense_real_time(state):
    now = datetime.now().isoformat()
    s = state.setdefault("signals", {
        "weather_temp_c": 22.0,
        "weather_rain_prob": 0.2,
        "foot_traffic_idx": 0.5,
        "social_sentiment": 0.1,
    })
    s["weather_temp_c"] = _rand_trend(s["weather_temp_c"], 0, 40, 1.5)
    s["weather_rain_prob"] = _rand_trend(s["weather_rain_prob"], 0, 1, 0.15)
    s["foot_traffic_idx"] = _rand_trend(s["foot_traffic_idx"], 0, 1, 0.12)
    s["social_sentiment"] = _rand_trend(s["social_sentiment"], -1, 1, 0.1)
    s["timestamp"] = now
    return s

def think_plan(state, kpi_rows, channels):
    agg = {ch: {"clicks":0, "leads":0, "spend":0.0} for ch in channels}
    for r in kpi_rows[-len(channels)*3:]:
        ch = r["channel"]
        agg[ch]["clicks"] += int(r.get("clicks",0))
        agg[ch]["leads"] += int(r.get("orders", r.get("leads", 0) or 0))
        agg[ch]["spend"] += float(r.get("spend",0))
    scores = {}
    for ch, m in agg.items():
        ctr = (m["clicks"] / max(1, 3000))
        cac = (m["spend"] / max(1, m["leads"])) if m["leads"] else 999
        score = ctr - 0.0005 * cac
        scores[ch] = score
    bandit = state.setdefault("bandit", {})
    epsilon = state.setdefault("epsilon", 0.2)
    chosen = {}
    for ch in channels:
        b = bandit.setdefault(ch, {"A":{"reward":0.0,"n":0},"B":{"reward":0.0,"n":0}})
        if random.random() < epsilon:
            variant = random.choice(["A","B"])
        else:
            avgA = b["A"]["reward"]/max(1,b["A"]["n"])
            avgB = b["B"]["reward"]/max(1,b["B"]["n"])
            variant = "A" if avgA >= avgB else "B"
        chosen[ch] = variant
    exps = {ch: math.exp(3*scores.get(ch,0)) for ch in channels}
    total = sum(exps.values()) or 1.0
    weights = {ch: exps[ch]/total for ch in channels}
    plan = {"weights": weights, "creative": chosen, "scores": scores}
    state["last_plan"] = plan
    return plan

def act_apply(plan, budget_total, channels):
    per_day_total = budget_total/14.0
    rows = []
    for day in range(1, 15):
        for ch in channels:
            alloc = round(per_day_total * plan["weights"].get(ch, 1/len(channels)), 2)
            rows.append({"channel":ch,"day":day,"daily_budget":alloc,"creative":plan["creative"].get(ch,"A")})
    out = os.path.join(OUTPUT_DIR, "campaign_budget.csv")
    with open(out,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["channel","day","daily_budget","creative"])
        w.writeheader(); w.writerows(rows)
    return out

def learn_update(state, plan, kpi_rows):
    if not kpi_rows: return state
    last = kpi_rows[-1]
    ch = last["channel"]
    impressions = float(last.get("impressions", 3000))
    clicks = float(last.get("clicks", 60))
    orders = float(last.get("orders", 6))
    spend = float(last.get("spend", 120.0))
    ctr = clicks / max(1.0, impressions)
    cpa = spend / max(1.0, orders)
    reward = ctr - 0.0005*cpa
    chosen = plan["creative"].get(ch, "A")
    b = state.setdefault("bandit", {}).setdefault(ch, {"A":{"reward":0.0,"n":0},"B":{"reward":0.0,"n":0}})
    b[chosen]["reward"] += reward
    b[chosen]["n"] += 1
    return state

def policy_rules(signals):
    actions = []
    if signals["weather_rain_prob"] > 0.6:
        actions.append("Promote delivery offers (rainy) — add free delivery banner for 48h.")
    if signals["weather_temp_c"] >= 28:
        actions.append("Boost iced drinks creative; add discount code ICE10.")
    if signals["foot_traffic_idx"] > 0.7:
        actions.append("Shift budget to in-store promos; highlight table reservations.")
    if signals["social_sentiment"] < -0.3:
        actions.append("Trigger customer-care playbook; respond to negative reviews.")
    return actions

def regenerate_ads(company, channels, chosen):
    for ch in channels:
        variant = chosen.get(ch,"A")
        if ch.lower() == "instagram":
            copy = f"# Instagram Ads ({variant}) — {company}\nHeadline: {'Skip the line ☕' if variant=='A' else 'Your coffee, your way'}\nBody: {'Order online — pickup in 5 minutes.' if variant=='A' else 'Personalized drinks, delivered fast.'}\nCTA: {'Try it now' if variant=='A' else 'Order today'}"
            write_markdown("ads_instagram.md", copy)
        elif ch.lower() == "google":
            copy = f"# Google Ads ({variant}) — {company}\nHeadline: {'Order Coffee Online' if variant=='A' else 'Reserve Your Table'}\nDesc: {'2-minute order. 5-minute pickup.' if variant=='A' else 'Book a table, skip the wait.'}"
            write_markdown("ads_google.md", copy)
        elif ch.lower() == "linkedin":
            copy = f"# LinkedIn Ads ({variant}) — {company}\nHeadline: {'Fuel your standups' if variant=='A' else 'Coffee for teams'}\nBody: {'Office pickup powered by AI Virtual Café.' if variant=='A' else 'Subscriptions for teams & meetings.'}"
            write_markdown("ads_linkedin.md", copy)

# ---------- Analytics Helpers ----------
def load_kpis_df():
    path = os.path.join(OUTPUT_DIR, "campaign_kpis.csv")
    if not os.path.exists(path):
        import pandas as pd
        df = pd.DataFrame([
            {"day":1,"channel":"Google","impressions":3000,"clicks":60,"orders":6,"spend":120.0},
            {"day":1,"channel":"Instagram","impressions":3000,"clicks":60,"orders":6,"spend":120.0},
            {"day":1,"channel":"LinkedIn","impressions":3000,"clicks":60,"orders":6,"spend":120.0},
        ])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

def compute_metrics(df):
    df = df.copy()
    df["CTR"] = df["clicks"] / df["impressions"].clip(lower=1)
    df["CAC"] = df["spend"] / df["orders"].clip(lower=1)
    return df

def channel_options(df):
    chs = ["All"] + sorted(df["channel"].unique().tolist())
    return chs

# ---------- Streamlit UI ----------
st.title("☕ AI Virtual Café Demo")

tab1, tab2, tab3 = st.tabs(["🤖 Autonomy (Sense → Think → Act)", "📈 Analytics (KPIs)", "Artifacts"])

with tab1:
    st.subheader("Autonomous loop")
    channels = ["Google","Instagram","LinkedIn"]
    budget_total = st.number_input("Total budget ($)", value=5000)
    ticks = st.number_input("Steps", 1, 20, 3)
    run_btn = st.button("Run Autonomy Loop")
    if run_btn:
        kpi_path = os.path.join(OUTPUT_DIR, "campaign_kpis.csv")
        kpis = []
        if os.path.exists(kpi_path):
            with open(kpi_path) as f:
                r = csv.DictReader(f)
                for row in r:
                    row["clicks"] = int(row.get("clicks",0))
                    row["orders"] = int(row.get("orders",0))
                    row["spend"] = float(row.get("spend",0))
                    row["channel"] = row.get("channel","Google")
                    row["impressions"] = int(row.get("impressions",3000))
                    kpis.append(row)
        state = st.session_state.setdefault("autonomy", {})
        action_log = []
        for step in range(int(ticks)):
            sig = sense_real_time(state)
            plan = think_plan(state, kpis, channels)
            budget_file = act_apply(plan, budget_total, channels)
            state = learn_update(state, plan, kpis)
            acts = policy_rules(sig)
            regenerate_ads("AI Virtual Café", channels, plan["creative"])
            action_log.append({"step": step+1,"signals": sig,"actions": acts,"plan": plan,"budget_file": budget_file})
        st.success("Completed steps")
        for entry in action_log:
            st.json(entry)

with tab2:
    st.subheader("Campaign KPI Dashboard")
    df = compute_metrics(load_kpis_df())
    chs = channel_options(df)
    sel = st.selectbox("Channel", chs)
    if sel != "All":
        view = df[df["channel"] == sel].copy()
    else:
        view = df.groupby("day", as_index=False).agg({"impressions":"sum","clicks":"sum","orders":"sum","spend":"sum"})
        view["CTR"] = view["clicks"]/view["impressions"].clip(lower=1)
        view["CAC"] = view["spend"]/view["orders"].clip(lower=1)
    st.line_chart(view.set_index("day")["CTR"])
    st.line_chart(view.set_index("day")["CAC"])
    st.dataframe(view.tail(10))

with tab3:
    st.subheader("Artifacts")
    for fname in ["prd.md","instagram_plan.md","ads_instagram.md","ads_google.md","ads_linkedin.md","terms.txt","landing.html","sales_playbook.md","finance_model.md"]:
        path = os.path.join(OUTPUT_DIR,fname)
        if os.path.exists(path):
            st.markdown(f"### {fname}")
            st.code(open(path).read()[:500])
