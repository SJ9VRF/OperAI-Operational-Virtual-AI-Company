# streamlit_app.py
# OperAI — Virtual Company (Premium Demo UI)
# Elegant glass UI • Role filters & favorites • Task Execution (Kanban + Progress) • Advanced KPIs • Comms Hub
# Run: streamlit run streamlit_app.py

import streamlit as st
import random, textwrap, json
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict

st.set_page_config(page_title="OperAI — Virtual Company", page_icon="🤖", layout="wide")

# =========================
# Global Styles (Premium UI)
# =========================
GLOBAL_CSS = """
<style>
:root{
  --glass-bg: rgba(255,255,255,0.65);
  --glass-border: rgba(148,163,184,0.28);
  --shadow: 0 10px 30px rgba(2,6,23,0.10);
}
[data-theme="dark"] :root{
  --glass-bg: rgba(2,6,23,0.35);
  --glass-border: rgba(148,163,184,0.20);
  --shadow: 0 10px 30px rgba(0,0,0,0.40);
}
.main .block-container {padding-top: 0.8rem; padding-bottom: 3rem;}
/* Banner */
.operai-banner {
  border-radius: 18px;
  padding: 22px 26px;
  margin: 8px 0 18px 0;
  background: linear-gradient(135deg, rgba(59,130,246,0.20) 0%, rgba(16,185,129,0.16) 100%);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow);
}
/* Quick actions row */
.qa {display:flex; gap:10px; flex-wrap:wrap; margin-top:10px}
.qa a, .qa button {
  border-radius: 999px; border:1px solid var(--glass-border);
  background: var(--glass-bg); padding:8px 12px; cursor:pointer;
  transition: all .15s ease; font-size:0.88rem;
}
.qa a:hover, .qa button:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
/* Cards */
.card {
  border-radius: 16px; padding: 16px 16px; background: var(--glass-bg);
  border: 1px solid var(--glass-border); box-shadow: var(--shadow); margin-bottom: 14px;
  transition: transform .12s ease;
}
.card:hover { transform: translateY(-1px); }
.hr-soft {
  border: none; height: 1px; background: linear-gradient(to right, transparent, rgba(148,163,184,0.35), transparent);
  margin: 10px 0 14px;
}
/* Chips & badges */
.chips {display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 0}
.chip {
  font-size: 0.75rem; line-height: 1;
  padding: 6px 10px; border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(148,163,184,0.10);
}
.badge {
  display:inline-block; padding:5px 10px; border-radius:999px;
  font-size:0.80rem; border:1px solid var(--glass-border); background: rgba(59,130,246,0.12);
}
.muted { opacity: .85; }
.kpill {display:flex; align-items:center; gap:8px}
.kpill .dot{width:8px;height:8px;border-radius:999px;background:rgba(16,185,129,.9)}
/* Kanban */
.kanban {display:grid; grid-template-columns: repeat(4,1fr); gap:12px}
.kanban .kcol {background: var(--glass-bg); border:1px solid var(--glass-border); border-radius:14px; padding:12px; box-shadow: var(--shadow);}
.kcol h5{margin:0 0 8px 0}
.kcard{border:1px dashed var(--glass-border); border-radius:12px; padding:8px 10px; margin-bottom:8px; font-size:0.92rem}
.kcount{font-size:0.8rem; opacity:.8}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# =========================
# Session bootstrap
# =========================
def ensure_state():
    ss = st.session_state
    ss.setdefault("founder_name", "")
    ss.setdefault("business_needs", "")
    ss.setdefault("agents", [])
    ss.setdefault("timeline_df", pd.DataFrame())
    ss.setdefault("execution_progress", {})  # task execution engine
    ss.setdefault("kpis", {})
    ss.setdefault("seed", 42)
    ss.setdefault("chats", {})             # {agent_id: [...]}
    ss.setdefault("last_updates", {})      # {agent_id: "status"}
    ss.setdefault("emails", {})            # {agent_id: "email"}
    ss.setdefault("favorites", set())      # pinned agent_id
    # Navigation helpers
    ss.setdefault("nav", "1) Founder")
    ss.setdefault("comms_target_agent", None)
    ss.setdefault("comms_active_tab", "Chat")
ensure_state()
random.seed(st.session_state.seed)

# =========================
# Role library (+ categories)
# =========================
ROLE_LIBRARY: Dict[str, Dict] = {
    # Core ops/gtm
    "ops_manager": {"title":"Operations Manager","cat":"Operations",
        "skills":["SOPs","Capacity","Scheduling","QA"],
        "tools":["Notion","WhenIWork","Slack"],
        "tasks":["Draft SOPs","Plan capacity","Publish schedules","Run QA audits"],
        "about":"Sets operating rhythm, staffing, and quality loops."},
    "ads": {"title":"Ad Campaign Specialist","cat":"Marketing",
        "skills":["Targeting","Budget","Attribution","A/B"],
        "tools":["Meta Ads","Google Ads","GA4"],
        "tasks":["Define audiences","Launch campaigns","A/B creatives","Optimize ROAS"],
        "about":"Finds customers efficiently and scales paid performance."},
    "content": {"title":"Content Creator","cat":"Marketing",
        "skills":["Copy","Design","Short-form video"],
        "tools":["Canva","Figma","CapCut"],
        "tasks":["Promo images/video","Ad & landing copy","Menu highlights","Schedule posts"],
        "about":"Turns offers into engaging visuals aligned with brand voice."},
    "social": {"title":"Social Media Manager","cat":"Marketing",
        "skills":["Calendar","Community","Analytics"],
        "tools":["Instagram","TikTok","Buffer"],
        "tasks":["Weekly calendar","Publish posts","Reply DMs","Track engagement"],
        "about":"Grows organic reach and manages community touchpoints."},
    "reservations": {"title":"Reservation Agent","cat":"Reservations",
        "skills":["Seating rules","CRM","Reminders"],
        "tools":["OpenTable","Resy","Twilio"],
        "tasks":["Integrate widget","Confirm bookings","Reminders","No-show analysis"],
        "about":"Keeps the house full with smart confirmations and seating."},
    "reservation_site_manager": {"title":"Reservation Site Manager","cat":"Reservations",
        "skills":["Widget UX","Seating policies","Conversion"],
        "tools":["OpenTable/Resy Admin","Hotjar","GA4"],
        "tasks":["Design booking funnel UX","Seating/party-size rules","A/B reservation CTAs","Conv tracking"],
        "about":"Owns the reservation experience and boosts conversions."},
    "booking_integration_engineer": {"title":"Booking Integration Engineer","cat":"Reservations",
        "skills":["APIs","Webhooks","Calendar"],
        "tools":["OpenTable/Resy APIs","Zapier","Calendars"],
        "tasks":["Connect booking APIs","Sync calendars","Automate confirmations","Emit analytics events"],
        "about":"Makes reservations integrated & observable via events."},
    "ordering_platform_manager": {"title":"Online Ordering Platform Manager","cat":"Ordering",
        "skills":["Funnel design","Promos","Channel sync"],
        "tools":["Toast/Square Online","DoorDash/UberEats","GA4"],
        "tasks":["Optimize checkout funnel","Configure promos","Sync menus","Track conversion"],
        "about":"Owns online ordering funnel and channel parity."},
    "online_ordering": {"title":"Online Ordering Manager","cat":"Ordering",
        "skills":["POS integration","Menu sync","Order routing"],
        "tools":["Square/Toast","Shopify","Zapier"],
        "tasks":["Connect POS & payments","Publish menu","Order notifications","Checkout QA"],
        "about":"Runs menu→checkout→payment pipeline."},
    "pos_integration_engineer": {"title":"POS Integration Engineer","cat":"Ordering",
        "skills":["Auth","Catalog sync","Payments"],
        "tools":["Toast/Square APIs","Stripe","Webhook relays"],
        "tasks":["Map POS catalog","Sync prices/modifiers","Harden callbacks","Latency/failure analysis"],
        "about":"Guarantees data parity and reliable payments."},
    "customer_notifications_manager": {"title":"Customer Notifications Manager","cat":"CX",
        "skills":["Email/SMS","Templates","Segmentation"],
        "tools":["Twilio/Sendgrid","Customer.io","Klaviyo"],
        "tasks":["Confirmations & reminders","ETA/pickup notifications","Win-back/VIP","No-show reduction"],
        "about":"Automated comms that reduce no-shows and drive reorders."},
    "delivery_ops": {"title":"Delivery Coordinator","cat":"Ordering",
        "skills":["Dispatch","Routing","SLA tracking"],
        "tools":["UberEats","DoorDash","Maps API"],
        "tasks":["Integrate partners","Zones/fees","Monitor ETAs","Improve on-time rate"],
        "about":"Optimizes last-mile logistics to hit SLAs."},
    "menu": {"title":"Menu Manager","cat":"Ordering",
        "skills":["Structuring","Pricing","Tags/Allergens"],
        "tools":["POS Editor","Sheets"],
        "tasks":["Categories","Upload items/prices","Add images/tags","Sync channels"],
        "about":"Ensures correct items & prices everywhere."},
    "finance": {"title":"Accountant","cat":"Finance",
        "skills":["P&L","Cash flow","Reconciliation"],
        "tools":["QuickBooks","Stripe","Xero"],
        "tasks":["Connect accounts","Chart of accounts","Weekly P&L","Forecast cash"],
        "about":"Surfaces unit economics and keeps cash predictable."},
    "procurement": {"title":"Procurement Officer","cat":"Ops",
        "skills":["Vendors","Inventory","Cost control"],
        "tools":["Vendor Portals","Email","Sheets"],
        "tasks":["Supplier list","Negotiate terms","Reorder points","Track waste"],
        "about":"Supply continuity at best landed cost."},
    "cx_lead": {"title":"Customer Experience Lead","cat":"CX",
        "skills":["Support","NPS/CSAT","Playbooks"],
        "tools":["Intercom","HelpScout","Zendesk"],
        "tasks":["Set up inbox","Macros/playbooks","NPS program","Refund handling"],
        "about":"Owns voice of customer and loyalty."},
    "data_analyst": {"title":"Data Analyst","cat":"Data",
        "skills":["SQL","Dashboards","Forecasting"],
        "tools":["BigQuery","Looker/Metabase","Sheets"],
        "tasks":["KPI dashboards","Cohorts/retention","Promo analysis","Demand forecast"],
        "about":"Turns data into decisions with clear visuals."},
    "qa_automation": {"title":"QA Automation","cat":"Engineering",
        "skills":["E2E tests","Monitoring","Alerting"],
        "tools":["Playwright","Postman","PagerDuty"],
        "tasks":["Checkout tests","Endpoint monitors","SLOs & alerts","Uptime reports"],
        "about":"Prevents silent failures with synthetic testing."},
    "security": {"title":"Security & Compliance","cat":"Engineering",
        "skills":["Access control","PII hygiene","Vendor risk"],
        "tools":["SSO/OAuth","1Password","DLP"],
        "tasks":["Harden access","Vendor reviews","Retention rules","Phishing drills"],
        "about":"Reduces risk and keeps data protected."},
    "web_ops_engineer": {"title":"Web Ops Engineer (Res/Order)","cat":"Engineering",
        "skills":["CI/CD","Perf/SEO","Observability"],
        "tools":["Vercel/Netlify","Lighthouse","Sentry"],
        "tasks":["CI/CD for sites","Page speed/SEO","Error tracking","Blue/green rollouts"],
        "about":"Keeps sites fast, stable, and discoverable."},
    "seo_sem_specialist": {"title":"SEO/SEM Specialist (Bookings & Orders)","cat":"Marketing",
        "skills":["Keywords","Local SEO","Landing A/B"],
        "tools":["Search Console","GA4","Ads"],
        "tasks":["Local SEO for reservations","Ordering landing tests","Schema markup","Paid search alignment"],
        "about":"Drives high-intent traffic to booking & ordering."},
}

KEYWORD_TO_ROLES = {
    "reservation": ["reservations","reservation_site_manager","booking_integration_engineer","customer_notifications_manager","seo_sem_specialist","web_ops_engineer"],
    "reservations": ["reservations","reservation_site_manager","booking_integration_engineer","customer_notifications_manager","seo_sem_specialist","web_ops_engineer"],
    "booking": ["reservations","reservation_site_manager","booking_integration_engineer"],
    "online ordering": ["ordering_platform_manager","online_ordering","pos_integration_engineer","customer_notifications_manager","web_ops_engineer"],
    "ordering": ["ordering_platform_manager","online_ordering","pos_integration_engineer"],
    "delivery": ["delivery_ops","customer_notifications_manager"],
    "menu": ["menu","pos_integration_engineer"],
    "ads": ["ads","seo_sem_specialist","content"],
    "advertising": ["ads","seo_sem_specialist","content"],
    "seo": ["seo_sem_specialist","web_ops_engineer"],
    "sem": ["seo_sem_specialist"],
    "finance": ["finance"], "accounting": ["finance"],
    "procurement": ["procurement"],
    "customer": ["cx_lead","customer_notifications_manager"], "support": ["cx_lead"],
    "data": ["data_analyst"], "analytics": ["data_analyst"],
    "qa": ["qa_automation"], "security": ["security"],
    "ops": ["ops_manager","web_ops_engineer"],
}

DEFAULT_ROLE_KEYS_FOR_RESTAURANT = [
    "ops_manager","ads","content","social","reservations","menu","finance","procurement",
    "cx_lead","data_analyst","qa_automation","security","delivery_ops",
    "reservation_site_manager","booking_integration_engineer","ordering_platform_manager",
    "pos_integration_engineer","customer_notifications_manager","web_ops_engineer","seo_sem_specialist",
    "online_ordering",
]

# =========================
# Avatars
# =========================
def initials_avatar(name: str, badge: str, size: int = 160):
    palette = ["#4B8BF4","#10B981","#F59E0B","#EC4899","#8B5CF6","#06B6D4"]
    bg = random.choice(palette)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    d.ellipse([4,4,size-4,size-4], outline="#ffffff", width=6)
    initials = "".join([p[0] for p in name.split()[:2]]).upper() or "AI"
    try:
        font = ImageFont.truetype("Arial.ttf", int(size*0.45))
        small = ImageFont.truetype("Arial.ttf", int(size*0.14))
    except:
        font = ImageFont.load_default(); small = ImageFont.load_default()
    w,h = d.textbbox((0,0), initials, font=font)[2:]
    d.text(((size-w)/2, (size-h)/2-8), initials, fill="white", font=font)
    label = badge.split()[0][:10].upper()
    bw,bh = d.textbbox((0,0), label, font=small)[2:]
    pad = 6
    d.rectangle([10, size-(bh+pad*2)-10, 10+bw+12, size-10], fill=(0,0,0,160))
    d.text((16, size-(bh+pad*2)-10+pad), label, fill="white", font=small)
    return img

def fake_name():
    first = random.choice(["Sophia","Liam","Olivia","Noah","Ava","Ethan","Mia","Lucas","Isabella","Leo","Amelia","Mason","Chloe","Aiden","Zoe","Aria","Ella","Luna","Nora","Kai"])
    last  = random.choice(["Lopez","Kim","Patel","Rodriguez","Nguyen","Smith","Chen","Garcia","Singh","Brown","Khan","Hernandez","Wang","Davis","Martinez","Wilson","Anderson","Clark"])
    return f"{first} {last}"

AGENT_EMAIL_DOMAIN = "operai.ai"

def make_agent(role_key: str) -> Dict:
    role = ROLE_LIBRARY[role_key]
    name = fake_name()
    email = f"{name.lower().replace(' ','.')}@{AGENT_EMAIL_DOMAIN}"
    avatar = initials_avatar(name, role["title"])
    agent_id = f"{role_key}-{random.randint(1000,9999)}"
    st.session_state.emails[agent_id] = email
    st.session_state.chats.setdefault(agent_id, [
        {"role": "agent", "text": f"Hi, I'm {name}, your {role['title']}. How can I help today?", "ts": str(datetime.now())}
    ])
    return {
        "id": agent_id, "name": name, "email": email,
        "role_key": role_key, "title": role["title"], "cat": role["cat"],
        "skills": role["skills"], "tools": role["tools"], "tasks": role["tasks"],
        "about": role.get("about",""),
        "avatar": avatar,
    }

# =========================
# Needs → roles
# =========================
def extract_roles_from_needs(needs: str) -> List[str]:
    needs_lc = needs.lower()
    selected = set()
    for k, roles in KEYWORD_TO_ROLES.items():
        if k in needs_lc:
            selected.update(roles)
    if not selected:
        selected.update(DEFAULT_ROLE_KEYS_FOR_RESTAURANT)
    return list(selected)

def generate_team(needs: str) -> List[Dict]:
    role_keys = extract_roles_from_needs(needs)
    random.shuffle(role_keys)
    role_keys = role_keys[:20]  # cap for UI
    return [make_agent(k) for k in role_keys]

# =========================
# Timeline / Gantt
# =========================
def build_timeline(agents: List[Dict]) -> pd.DataFrame:
    start = datetime.today().date()
    rows = []
    for ag in agents:
        for idx, task in enumerate(ag["tasks"]):
            week = (idx % 4) + 1
            sd = start + timedelta(days=(week-1)*7 + random.randint(0,2))
            ed = sd + timedelta(days=2 + random.randint(0,2))
            rows.append({"Agent": ag["name"], "Role": ag["title"], "Task": task,
                         "Start": pd.to_datetime(sd), "End": pd.to_datetime(ed), "Week": week})
    df = pd.DataFrame(rows)
    return df.sort_values(["Start","Agent","Task"]).reset_index(drop=True)

def gantt_chart(df: pd.DataFrame):
    if df.empty:
        st.info("Timeline is empty."); return
    chart = alt.Chart(df).mark_bar().encode(
        x="Start:T", x2="End:T",
        y=alt.Y("Agent:N", sort="-x"),
        color=alt.Color("Week:N", legend=None),
        tooltip=["Agent","Role","Task","Start","End","Week"]
    ).properties(height=480)
    st.altair_chart(chart, use_container_width=True)

# =========================
# Task Execution Engine + KPIs
# =========================
def initialize_execution(df: pd.DataFrame):
    prog = {}
    for _, row in df.iterrows():
        prog[f"{row.Agent}:{row.Task}"] = random.randint(0, 18)
    st.session_state.execution_progress = prog

def step_execution(ticks=1):
    prog = st.session_state.execution_progress
    for _ in range(ticks):
        for k in list(prog.keys()):
            prog[k] = min(100, prog[k] + random.randint(4, 12))
    st.session_state.execution_progress = prog

def stage_of(pct:int)->str:
    if pct >= 100: return "Done"
    if pct >= 70: return "Review"
    if pct >= 35: return "In Progress"
    return "Planned"

def compute_kpis(progress: Dict[str,int], agents: List[Dict]) -> Dict:
    total = len(progress); done = sum(1 for v in progress.values() if v >= 100)
    pct = int((done/total)*100) if total else 0
    orders = 120 + done*3 + random.randint(-8,12)
    on_time = min(99, 90 + done//3)
    roi = round(2.2 + done*0.02, 2)
    revenue = 3500 + done*75
    roles = {a["title"] for a in agents}
    if "Ad Campaign Specialist" in roles: roi += 0.2
    if "Delivery Coordinator" in roles: on_time = min(99, on_time + 1)
    if "Accountant" in roles: revenue += 150
    return {
        "Tasks Completed": f"{done}/{total} ({pct}%)",
        "Orders Today": max(0, orders),
        "On-Time Delivery": f"{on_time}%",
        "Campaign ROI": f"{roi}x",
        "Revenue": f"${int(revenue):,}"
    }

# =========================
# Meetings (.ics)
# =========================
def build_ics(agent_name: str, title: str, start_dt: datetime, duration_min: int, notes: str) -> str:
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_dt.strftime("%Y%m%dT%H%M%SZ")
    dtend   = (start_dt + timedelta(minutes=duration_min)).strftime("%Y%m%dT%H%M%SZ")
    uid = f"{random.randint(100000,999999)}@operai.ai"
    summary = title or f"Meeting with {agent_name}"
    description = notes.replace("\n","\\n")
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OperAI//Calendar 1.0//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""

# =========================
# Updates
# =========================
SAMPLE_UPDATES = [
    "Reservation CTA v2 outperforming by +9.8%.",
    "POS catalog sync successful (0 mismatches).",
    "Checkout funnel drop-off reduced by 6%.",
    "ETA SMS lowered cancellations by 11%.",
    "Webhooks stable; no drops in 24h window.",
    "Menu schema validated; rich results detected.",
    "PageSpeed improved after image optimization.",
    "A/B test: Landing B beating A by +7% CR.",
    "Security audit passed; access logs clean.",
    "QA synthetic order succeeded in staging.",
]
def get_fresh_update() -> str: return f"{datetime.now().strftime('%H:%M:%S')} — {random.choice(SAMPLE_UPDATES)}"
def record_agent_update(agent_id: str): st.session_state.last_updates[agent_id] = get_fresh_update()

# =========================
# Helpers (UI + Navigation)
# =========================
def jump_to(page: str):
    st.session_state.nav = page
    st.session_state.nav_radio = page

def jump_to_comms(agent_id: str, tab: str):
    st.session_state.comms_target_agent = agent_id
    st.session_state.comms_active_tab = tab  # "Chat" or "Meetings"
    jump_to("6) Comms")

def agent_card(ag: Dict):
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        top = st.columns([1,3,1])
        with top[0]:
            st.image(ag["avatar"], caption=ag["name"], use_container_width=True)
        with top[1]:
            st.subheader(ag["title"])
            st.markdown(f'<span class="badge">{ag["cat"]}</span>', unsafe_allow_html=True)
            st.write(ag["about"])
            st.markdown('<div class="chips">', unsafe_allow_html=True)
            for s in ag["skills"][:5]:
                st.markdown(f'<span class="chip">{s}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.expander("Responsibilities (Initial Plan)"):
                for t in ag["tasks"]:
                    st.write(f"• {t}")
        with top[2]:
            fav = ag["id"] in st.session_state.favorites
            if st.button(("★ Unpin" if fav else "☆ Pin"), key=f"fav_{ag['id']}"):
                if fav: st.session_state.favorites.remove(ag["id"])
                else: st.session_state.favorites.add(ag["id"])
                st.rerun()
            st.caption(f"`{ag['email']}`")

        actions = st.columns(3)
        if actions[0].button("💬 Chat", key=f"chat_{ag['id']}"): jump_to_comms(ag["id"], "Chat")
        if actions[1].button("📅 Meeting", key=f"meet_{ag['id']}"): jump_to_comms(ag["id"], "Meetings")
        if actions[2].button("🔄 Get Update", key=f"upd_{ag['id']}"):
            record_agent_update(ag["id"]); st.toast(f"Latest update pulled from {ag['name']}")
        upd = st.session_state.last_updates.get(ag["id"])
        if upd: st.caption(f"**Latest Update:** {upd}")
        st.markdown('</div>', unsafe_allow_html=True)

def sparkline(values, title):
    df = pd.DataFrame({"x": list(range(len(values))), "y": values})
    ch = alt.Chart(df).mark_line(point=False).encode(x="x:Q", y="y:Q").properties(height=60)
    st.caption(title)
    st.altair_chart(ch, use_container_width=True)

# =========================
# Sidebar + Banner + Quick Actions
# =========================
st.markdown("""
<div class="operai-banner">
  <h2 style="margin:0;">🤖 OperAI — The AI Virtual Company</h2>
  <div class="muted" style="margin-top:6px;">Autonomous agents for reservations & online ordering — coordinated, measurable, and always-on.</div>
  <div class="qa">
    <button onclick="window.location.href='#qa-generate'">Generate Team</button>
    <button onclick="window.location.href='#qa-timeline'">Timeline</button>
    <button onclick="window.location.href='#qa-exec'">Task Execution</button>
    <button onclick="window.location.href='#qa-kpi'">KPIs</button>
    <button onclick="window.location.href='#qa-comms'">Comms Hub</button>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Navigate")
st.session_state.nav = st.sidebar.radio(
    "",
    ["1) Founder","2) Team","3) Timeline","4) Task Execution","5) KPIs","6) Comms"],
    index=["1) Founder","2) Team","3) Timeline","4) Task Execution","5) KPIs","6) Comms"].index(st.session_state.nav),
    key="nav_radio"
)
st.sidebar.markdown("---")
st.sidebar.info("Tip: Pin favorites ★ and use per-agent Chat/Meeting/Get Update.")

# =========================
# Top Utility Row
# =========================
def top_filters():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3,2,2,2])
    q = c1.text_input("Search roles or skills", value=st.session_state.get("q",""))
    st.session_state.q = q
    cats = sorted({v["cat"] for v in ROLE_LIBRARY.values()})
    pick = c2.multiselect("Filter by category", options=cats, default=st.session_state.get("pick",[]))
    st.session_state.pick = pick
    fav_only = c3.checkbox("Favorites only ★", value=st.session_state.get("fav_only", False))
    st.session_state.fav_only = fav_only
    # Export
    if c4.button("⬇️ Download Team JSON"):
        data = st.session_state.agents or []
        st.download_button("Download", data=json.dumps(data, default=str, indent=2),
                           file_name="operai_team.json", mime="application/json")
    st.markdown('</div>', unsafe_allow_html=True)

def filtered_agents():
    ags = st.session_state.agents or []
    if st.session_state.get("q"):
        q = st.session_state.q.lower()
        ags = [a for a in ags if q in a["title"].lower() or any(q in s.lower() for s in a["skills"]) or q in a["cat"].lower()]
    if st.session_state.get("pick"):
        ags = [a for a in ags if a["cat"] in st.session_state.pick]
    if st.session_state.get("fav_only"):
        ags = [a for a in ags if a["id"] in st.session_state.favorites]
    return ags

# =========================
# Pages
# =========================
# 1) Founder
if st.session_state.nav.startswith("1"):
    st.markdown('<a name="qa-generate"></a>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Founder Input")
        st.write("Describe your business. OperAI will generate a reservations/ordering-focused AI team with timeline, task execution, KPIs, and a comms hub.")
        st.session_state.founder_name = st.text_input("Founder Name", value=st.session_state.founder_name or "Alice Founder")
        placeholder = textwrap.dedent("""
            I opened a restaurant and need an online reservation site, booking confirmations, calendar sync,
            and an online ordering funnel with POS integration, promos, delivery coordination, SEO/SEM, and QA/security.
        """).strip()
        st.session_state.business_needs = st.text_area("Business Needs", value=st.session_state.business_needs or placeholder, height=150)
        colg1, colg2 = st.columns([1,1])
        if colg1.button("Generate My AI Team ▶"):
            st.session_state.agents = generate_team(st.session_state.business_needs)
            st.session_state.timeline_df = build_timeline(st.session_state.agents)
            initialize_execution(st.session_state.timeline_df)
            st.success("Your team is ready! Open **Team**, **Timeline**, **Task Execution**, **KPIs**, or **Comms**.")
        if colg2.button("Reset All"):
            for k in ["agents","timeline_df","execution_progress","kpis","chats","last_updates","favorites"]:
                st.session_state[k] = [] if k in ["agents"] else (pd.DataFrame() if k=="timeline_df" else {} if k!="favorites" else set())
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 2) Team
elif st.session_state.nav.startswith("2"):
    st.subheader("Your AI Team — Advanced Profiles")
    if not st.session_state.agents:
        st.warning("No team yet. Go to **Founder** and click **Generate My AI Team**.")
    else:
        top_filters()
        ags = filtered_agents()
        if not ags:
            st.info("No roles match your filter.")
        else:
            cols = st.columns(2)
            for i, ag in enumerate(ags):
                with cols[i % 2]:
                    agent_card(ag)

# 3) Timeline
elif st.session_state.nav.startswith("3"):
    st.markdown('<a name="qa-timeline"></a>', unsafe_allow_html=True)
    st.subheader("Project Timeline")
    if st.session_state.timeline_df.empty:
        st.warning("No timeline yet. Generate your team first.")
    else:
        st.caption("4-week roadmap (color by week). Hover for details.")
        gantt_chart(st.session_state.timeline_df)
        with st.expander("Table View"):
            st.dataframe(st.session_state.timeline_df, use_container_width=True)

# 4) Task Execution
elif st.session_state.nav.startswith("4"):
    st.markdown('<a name="qa-exec"></a>', unsafe_allow_html=True)
    st.subheader("Task Execution")
    if not st.session_state.execution_progress:
        st.warning("Initialize by generating a team and timeline.")
    else:
        # Kanban snapshot
        stages = {"Planned":[], "In Progress":[], "Review":[], "Done":[]}
        for task_id, pct in st.session_state.execution_progress.items():
            stages[stage_of(pct)].append((task_id, pct))
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### Kanban Snapshot")
            st.markdown('<div class="kanban">', unsafe_allow_html=True)
            for name in ["Planned","In Progress","Review","Done"]:
                st.markdown('<div class="kcol">', unsafe_allow_html=True)
                st.markdown(f"<h5>{name} <span class='kcount'>({len(stages[name])})</span></h5>", unsafe_allow_html=True)
                for tid, pct in sorted(stages[name], key=lambda x: -x[1])[:8]:
                    st.markdown(f"<div class='kcard'>{tid.split(':')[1]} — <b>{pct}%</b></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

            left, right = st.columns([2,1])
            with left:
                st.caption("Advance cycles to progress tasks.")
                if st.button("Advance 5 Ticks ▶"):
                    step_execution(5); st.rerun()
                st.markdown("### In-flight Tasks (sample)")
                for task_id, pct in list(st.session_state.execution_progress.items())[:16]:
                    st.progress(pct, text=f"{task_id} — {pct}%")
            with right:
                st.markdown("### Controls")
                n = st.number_input("Advance N ticks", min_value=1, max_value=300, value=12, step=1)
                if st.button("Advance"):
                    step_execution(n); st.rerun()
                if st.button("Reset Execution"):
                    initialize_execution(st.session_state.timeline_df); st.success("Execution state reset."); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# 5) KPIs
elif st.session_state.nav.startswith("5"):
    st.markdown('<a name="qa-kpi"></a>', unsafe_allow_html=True)
    st.subheader("KPI Dashboard")
    if not st.session_state.agents or not st.session_state.execution_progress:
        st.warning("Generate your team and start task execution first.")
    else:
        k = compute_kpis(st.session_state.execution_progress, st.session_state.agents)
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Tasks Completed", k["Tasks Completed"])
            c2.metric("Orders Today", k["Orders Today"])
            c3.metric("On-Time Delivery", k["On-Time Delivery"])
            c4.metric("Campaign ROI", k["Campaign ROI"])
            c5.metric("Revenue", k["Revenue"])
            st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)
            s1, s2, s3 = st.columns(3)
            sparkline([random.randint(60,100) for _ in range(12)], "Booking Conversion (12h)")
            with s1: sparkline([random.randint(40,120) for _ in range(14)], "Orders per Hour")
            with s2: sparkline([random.randint(80,98) for _ in range(14)], "On-Time % Trend")
            with s3: sparkline([round(1.8 + i*0.03 + random.random()*0.05,2) for i in range(14)], "Campaign ROI Trend")
            st.markdown('</div>', unsafe_allow_html=True)

# 6) Comms
elif st.session_state.nav.startswith("6"):
    st.markdown('<a name="qa-comms"></a>', unsafe_allow_html=True)
    st.subheader("Comms Hub — Contact • Chat • Meetings • Updates")
    if not st.session_state.agents:
        st.warning("No team yet. Go to **Founder** and generate your team.")
    else:
        tabs = st.tabs(["Directory","Chat","Meetings","Latest Updates"])

        # Directory (cards + actions, with filters)
        with tabs[0]:
            top_filters()
            ags = filtered_agents()
            if not ags: st.info("No roles match your filter.")
            cols = st.columns(2)
            for i, ag in enumerate(ags):
                with cols[i % 2]:
                    agent_card(ag)

        # Chat (selected agent)
        with tabs[1]:
            agent_names = {ag["id"]: f"{ag['name']} — {ag['title']}" for ag in st.session_state.agents}
            default_agent = st.session_state.comms_target_agent or list(agent_names.keys())[0]
            sel_idx = list(agent_names.keys()).index(default_agent) if default_agent in agent_names else 0
            sel = st.selectbox("Choose an agent", options=list(agent_names.keys()),
                               index=sel_idx, format_func=lambda k: agent_names[k], key="chat_sel")
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"#### Chat with {agent_names[sel]}")
                history = st.session_state.chats.get(sel, [])
                for msg in history[-14:]:
                    who = "You" if msg["role"]=="user" else "Agent"
                    st.markdown(f"**{who} ({msg['ts']}):** {msg['text']}")
                user_msg = st.text_input("Type your message", key=f"chat_input_{sel}")
                c1,c2,c3 = st.columns(3)
                if c1.button("Send"):
                    if user_msg.strip():
                        st.session_state.chats[sel].append({"role":"user","text":user_msg.strip(),"ts":str(datetime.now())})
                        reply = random.choice([
                            "Acknowledged. I’ll proceed and update KPIs.",
                            "On it — coordinating with linked roles now.",
                            "Copy. I’ll push a change and monitor metrics.",
                            "Starting. Expect a draft shortly.",
                        ])
                        st.session_state.chats[sel].append({"role":"agent","text":reply,"ts":str(datetime.now())})
                        st.session_state.comms_target_agent = sel
                        st.rerun()
                if c2.button("Clear Chat"):
                    st.session_state.chats[sel] = [{"role":"agent","text":"Chat reset. How can I help?","ts":str(datetime.now())}]
                    st.rerun()
                if c3.button("🔄 Get Update (this agent)"):
                    record_agent_update(sel); st.toast(f"Latest update pulled from {agent_names[sel]}")
                upd = st.session_state.last_updates.get(sel)
                if upd: st.caption(f"**Latest Update:** {upd}")
                st.markdown('</div>', unsafe_allow_html=True)

        # Meetings
        with tabs[2]:
            agent_names = {ag["id"]: f"{ag['name']} — {ag['title']}" for ag in st.session_state.agents}
            default_agent = st.session_state.comms_target_agent or list(agent_names.keys())[0]
            sel_idx = list(agent_names.keys()).index(default_agent) if default_agent in agent_names else 0
            sel = st.selectbox("Choose an agent", options=list(agent_names.keys()),
                               index=sel_idx, format_func=lambda k: agent_names[k], key="meet_sel")
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                mt_title = st.text_input("Meeting Title", value="Reservations/Ordering Sync")
                col_a, col_b = st.columns(2)
                date_val = col_a.date_input("Date", value=datetime.now().date())
                time_val = col_b.time_input("Start Time", value=(datetime.now()+timedelta(minutes=15)).time())
                duration = st.number_input("Duration (minutes)", min_value=15, max_value=180, value=30, step=15)
                notes = st.text_area("Notes/Agenda", value="Status, blockers, metrics, next steps.")
                if st.button("Create Calendar Invite (.ics)"):
                    agent_obj = next(a for a in st.session_state.agents if a["id"] == sel)
                    start_dt = datetime.combine(date_val, time_val)
                    ics = build_ics(agent_obj["name"], mt_title, start_dt, duration, notes)
                    fname = f"meeting_{agent_obj['name'].lower().replace(' ','_')}_{start_dt.strftime('%Y%m%dT%H%M')}.ics"
                    st.download_button("Download Invite", data=ics, file_name=fname, mime="text/calendar")
                    st.success(f"Invite prepared for {agent_obj['name']}.")
                st.markdown('</div>', unsafe_allow_html=True)

        # Latest Updates (bulk)
        with tabs[3]:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Get Latest Updates from All Agents")
                cols = st.columns([1,1,2])
                if cols[0].button("Get All Updates 🔄"):
                    for ag in st.session_state.agents: record_agent_update(ag["id"])
                    st.success("Updates received.")
                if cols[1].button("Clear Updates"):
                    st.session_state.last_updates = {}; st.rerun()
                for ag in st.session_state.agents:
                    upd = st.session_state.last_updates.get(ag["id"], "No update yet.")
                    st.write(f"**{ag['name']} — {ag['title']}**: {upd}")
                st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="muted" style="margin-top:14px;">© OperAI — Premium Demo UI</div>', unsafe_allow_html=True)
