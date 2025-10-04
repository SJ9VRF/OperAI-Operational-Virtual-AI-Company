# streamlit_app.py
# OperAI — AI Virtual Company (Streamlit, single-file demo)
# Premium UI • Planner→DAG • Execution State Machine • Business OS Modules • Comms Hub
# v2: Multi-location • Inventory/Vendors • HR/Compliance • Loyalty/CRM • Experiments • Data Pipes • Save/Load

import streamlit as st
import random, textwrap, json, uuid, base64, io
from datetime import datetime, timedelta, date, time
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional

st.set_page_config(page_title="OperAI — AI Virtual Company", page_icon="🤖", layout="wide")

# ===========
# Global CSS
# ===========
CSS = """
<style>
:root{ --glass-bg: rgba(255,255,255,0.65); --glass-border: rgba(148,163,184,0.28); --shadow:0 10px 30px rgba(2,6,23,0.10);}
[data-theme="dark"] :root{ --glass-bg: rgba(2,6,23,0.35); --glass-border: rgba(148,163,184,0.20); --shadow: 0 10px 30px rgba(0,0,0,0.40); }
.main .block-container{padding-top:.6rem; padding-bottom:3rem;}
.operai-banner{ border-radius:18px; padding:22px 26px; margin:6px 0 14px; background:linear-gradient(135deg, rgba(59,130,246,.20) 0%, rgba(16,185,129,.16) 100%); border:1px solid var(--glass-border); box-shadow:var(--shadow);}
.qa{display:flex; gap:10px; flex-wrap:wrap; margin-top:10px}
.qa button{ border-radius:999px; border:1px solid var(--glass-border); background:var(--glass-bg); padding:8px 12px; cursor:pointer; transition:all .15s ease; font-size:.88rem;}
.qa button:hover{ transform:translateY(-1px); box-shadow:var(--shadow);}
.card{ border-radius:16px; padding:16px 16px; background:var(--glass-bg); border:1px solid var(--glass-border); box-shadow:var(--shadow); margin-bottom:14px; transition:transform .12s ease;}
.card:hover{ transform:translateY(-1px);}
.hr-soft{ border:none; height:1px; background:linear-gradient(to right, transparent, rgba(148,163,184,.35), transparent); margin:10px 0 14px}
.chips{display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 0}
.chip{ font-size:.75rem; line-height:1; padding:6px 10px; border-radius:999px; border:1px solid var(--glass-border); background:rgba(148,163,184,.10)}
.badge{ display:inline-block; padding:5px 10px; border-radius:999px; font-size:.80rem; border:1px solid var(--glass-border); background:rgba(59,130,246,.12)}
.muted{ opacity:.85;}
.kanban{display:grid; grid-template-columns:repeat(4,1fr); gap:12px}
.kcol{background:var(--glass-bg); border:1px solid var(--glass-border); border-radius:14px; padding:12px; box-shadow:var(--shadow)}
.kcol h5{margin:0 0 8px 0}
.kcard{border:1px dashed var(--glass-border); border-radius:12px; padding:8px 10px; margin-bottom:8px; font-size:.92rem}
.kcount{font-size:.8rem; opacity:.8}
.small{font-size:.88rem}
.tablelike td, .tablelike th { padding: 6px 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ===========
# Boot state
# ===========
def ensure_state():
    ss = st.session_state
    ss.setdefault("founder_name", "")
    ss.setdefault("business_name", "")
    ss.setdefault("business_needs", "")
    ss.setdefault("agents", [])                   # list of dict
    ss.setdefault("favorites", set())             # pinned agents
    ss.setdefault("timeline_df", pd.DataFrame())  # tasks timeline
    ss.setdefault("execution", {})                # {task_id: {title, owner_id, status, progress, depends_on:[]}}
    ss.setdefault("workflows", {})                # {wf_id: {name, task_ids:[]}}
    ss.setdefault("blackboard", {})               # shared state
    ss.setdefault("chats", {})                    # {agent_id: [history]}
    ss.setdefault("last_updates", {})             # {agent_id: text}
    ss.setdefault("emails", {})                   # {agent_id: email}
    ss.setdefault("alerts", [])                   # [{ts, level, text}]
    ss.setdefault("q",""); ss.setdefault("pick",[]); ss.setdefault("fav_only", False)
    # Menu items
    if "menu_items" not in ss:
        ss.menu_items = pd.DataFrame([
            {"id": str(uuid.uuid4()), "name":"Margherita Pizza","category":"Pizza","price":12.0,"sku":"PZ001","tags":"veg","img":"","cost":3.8,"available":True},
            {"id": str(uuid.uuid4()), "name":"Spicy Wings","category":"Sides","price":8.5,"sku":"SD003","tags":"spicy","img":"","cost":2.6,"available":True},
            {"id": str(uuid.uuid4()), "name":"Caesar Salad","category":"Salad","price":9.0,"sku":"SL002","tags":"", "img":"","cost":2.2,"available":True},
        ])
    # Inventory (SKU-level)
    ss.setdefault("inventory", pd.DataFrame([
        {"sku":"PZ001","name":"Margherita Pizza","on_hand":42,"reorder_point":20,"lead_days":2,"vendor":"FreshDough Co"},
        {"sku":"SD003","name":"Spicy Wings","on_hand":30,"reorder_point":15,"lead_days":3,"vendor":"WingFarm"},
        {"sku":"SL002","name":"Caesar Salad","on_hand":25,"reorder_point":10,"lead_days":2,"vendor":"Greens&Co"},
    ]))
    # Vendors
    ss.setdefault("vendors", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"FreshDough Co","contact":"orders@freshdough.example","lead_days":2,"terms":"Net 15"},
        {"id":str(uuid.uuid4()),"name":"WingFarm","contact":"sales@wingfarm.example","lead_days":3,"terms":"Net 30"},
        {"id":str(uuid.uuid4()),"name":"Greens&Co","contact":"hello@greensco.example","lead_days":2,"terms":"Prepaid"},
    ]))
    # Locations
    ss.setdefault("locations", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"Aurora Bistro — Downtown","tz":"America/New_York","address":"123 Main St, NYC","open":"11:00","close":"22:00"},
        {"id":str(uuid.uuid4()),"name":"Aurora Bistro — Uptown","tz":"America/New_York","address":"500 Park Ave, NYC","open":"11:00","close":"22:00"},
    ]))
    # HR
    ss.setdefault("employees", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"Alex Rivera","role":"General Manager","location":"Downtown","status":"Active"},
        {"id":str(uuid.uuid4()),"name":"Kim Lee","role":"Shift Lead","location":"Uptown","status":"Active"},
    ]))
    # CRM / Loyalty
    ss.setdefault("crm_customers", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"Jordan S.","email":"jordan@example.com","segment":"VIP","visits_30d":3,"last_visit":str(date.today()-timedelta(days=4))},
        {"id":str(uuid.uuid4()),"name":"Sam P.","email":"sam@example.com","segment":"New","visits_30d":1,"last_visit":str(date.today()-timedelta(days=2))},
    ]))
    # Experiments
    ss.setdefault("experiments", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"CTA copy test","area":"Reservations","status":"Running","metric":"Widget→Confirm","uplift_pct":7.2},
        {"id":str(uuid.uuid4()),"name":"Promo banner","area":"Ordering","status":"Paused","metric":"Checkout CR","uplift_pct":3.1},
    ]))
    # Data Pipes (connectors)
    ss.setdefault("connectors", pd.DataFrame([
        {"id":str(uuid.uuid4()),"name":"Google Ads","type":"Marketing","status":"Connected"},
        {"id":str(uuid.uuid4()),"name":"Square POS","type":"POS","status":"Connected"},
        {"id":str(uuid.uuid4()),"name":"DoorDash","type":"Delivery","status":"Pending"},
    ]))
    # Nav
    ss.setdefault("nav", "1) Founder")
    ss.setdefault("comms_target_agent", None)
    ss.setdefault("seed", 42)
ensure_state()
random.seed(st.session_state.seed)

# ============
# Helpers: Avatars & (De)Serialize
# ============
def initials_avatar(name: str, badge: str, size: int = 160) -> Image.Image:
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

def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def b64_to_img(s: str) -> Image.Image:
    try:
        return Image.open(io.BytesIO(base64.b64decode(s)))
    except Exception:
        return initials_avatar("AI", "Agent")

def fake_name():
    first = random.choice(["Sophia","Liam","Olivia","Noah","Ava","Ethan","Mia","Lucas","Isabella","Leo","Amelia","Mason","Chloe","Aiden","Zoe","Aria","Ella","Luna","Nora","Kai"])
    last  = random.choice(["Lopez","Kim","Patel","Rodriguez","Nguyen","Smith","Chen","Garcia","Singh","Brown","Khan","Hernandez","Wang","Davis","Martinez","Wilson","Anderson","Clark"])
    return f"{first} {last}"

AGENT_EMAIL_DOMAIN = "operai.ai"

# =====================
# Role Library (extended)
# =====================
ROLE_LIBRARY: Dict[str, Dict] = {
    # Marketing
    "ads":  {"title":"Ad Campaign Specialist","cat":"Marketing","skills":["Targeting","Budget","Attribution","A/B"],"tools":["Meta Ads","Google Ads","GA4"],
             "tasks":["Define audiences","Launch campaigns","A/B creatives","Optimize ROAS"],"about":"Scales paid performance efficiently."},
    "content":{"title":"Content Creator","cat":"Marketing","skills":["Copy","Design","Short-form video"],"tools":["Canva","Figma","CapCut"],
             "tasks":["Promo images/video","Ad & landing copy","Menu highlights","Schedule posts"],"about":"Turns offers into engaging visuals."},
    "email_crm":{"title":"Email & CRM Manager","cat":"Marketing","skills":["Segmentation","Lifecycle","ESP"],"tools":["Klaviyo","Mailchimp"],
             "tasks":["Welcome series","Winbacks","VIP perks","A/B subject lines"],"about":"Drives LTV and loyalty via lifecycle."},
    "seo_sem_specialist":{"title":"SEO/SEM Specialist (Bookings & Orders)","cat":"Marketing","skills":["Keywords","Local SEO","Landing A/B"],"tools":["Search Console","GA4","Ads"],
             "tasks":["Local SEO for reservations","Ordering tests","Schema markup","Paid search alignment"],"about":"Drives high-intent traffic."},
    "social":{"title":"Social Media Manager","cat":"Marketing","skills":["Calendar","Community","Analytics"],"tools":["Instagram","TikTok","Buffer"],
             "tasks":["Weekly calendar","Publish posts","Reply DMs","Track engagement"],"about":"Grows organic reach and community."},
    # Reservations
    "reservations":{"title":"Reservation Agent","cat":"Reservations","skills":["Seating rules","CRM","Reminders"],"tools":["OpenTable","Resy","Twilio"],
             "tasks":["Integrate widget","Confirm bookings","Reminders","No-show analysis"],"about":"Maxes covers with smart confirmations."},
    "reservation_site_manager":{"title":"Reservation Site Manager","cat":"Reservations","skills":["Widget UX","Seating policies","Conversion"],"tools":["OpenTable Admin","Hotjar","GA4"],
             "tasks":["Design booking funnel","Seating/party-size rules","A/B reservation CTAs","Conv tracking"],"about":"Boosts booking conversion."},
    "booking_integration_engineer":{"title":"Booking Integration Engineer","cat":"Reservations","skills":["APIs","Webhooks","Calendar"],"tools":["OpenTable/Resy APIs","Zapier","Calendars"],
             "tasks":["Connect booking APIs","Sync calendars","Automate confirmations","Emit analytics events"],"about":"Integrates and instrument reservations."},
    # Ordering
    "ordering_platform_manager":{"title":"Online Ordering Platform Manager","cat":"Ordering","skills":["Funnel design","Promos","Channel sync"],"tools":["Toast/Square Online","DoorDash/UberEats","GA4"],
             "tasks":["Optimize checkout","Configure promos","Sync menus","Track conversion"],"about":"Owns ordering funnel & parity."},
    "online_ordering":{"title":"Online Ordering Manager","cat":"Ordering","skills":["POS integration","Menu sync","Order routing"],"tools":["Square/Toast","Shopify","Zapier"],
             "tasks":["Connect POS & payments","Publish menu","Order notifications","Checkout QA"],"about":"Runs menu→checkout→payment pipeline."},
    "pos_integration_engineer":{"title":"POS Integration Engineer","cat":"Ordering","skills":["Auth","Catalog sync","Payments"],"tools":["Toast/Square APIs","Stripe","Webhook relays"],
             "tasks":["Map POS catalog","Sync prices/modifiers","Harden callbacks","Latency analysis"],"about":"Ensures parity & reliable payments."},
    "delivery_ops":{"title":"Delivery Coordinator","cat":"Ordering","skills":["Dispatch","Routing","SLA tracking"],"tools":["UberEats","DoorDash","Maps API"],
             "tasks":["Integrate partners","Zones/fees","Monitor ETAs","Improve on-time rate"],"about":"Optimizes last-mile logistics."},
    "menu":{"title":"Menu Manager","cat":"Ordering","skills":["Structuring","Pricing","Allergens"],"tools":["POS Editor","Sheets"],
             "tasks":["Categories","Upload items/prices","Add images/tags","Sync channels"],"about":"Keeps items & prices correct everywhere."},
    # Ops/Finance/Data/Eng
    "ops_manager":{"title":"Operations Manager","cat":"Operations","skills":["SOPs","Capacity","Scheduling","QA"],"tools":["Notion","WhenIWork","Slack"],
             "tasks":["Draft SOPs","Plan capacity","Publish schedules","Run QA audits"],"about":"Sets rhythm, staffing & quality loops."},
    "finance":{"title":"Accountant","cat":"Finance","skills":["P&L","Cash flow","Reconciliation"],"tools":["QuickBooks","Stripe","Xero"],
             "tasks":["Connect accounts","Chart of accounts","Weekly P&L","Forecast cash"],"about":"Surfaces unit economics."},
    "procurement":{"title":"Procurement Officer","cat":"Operations","skills":["Vendors","Inventory","Cost control"],"tools":["Vendor Portals","Email","Sheets"],
             "tasks":["Supplier list","Negotiate terms","Reorder points","Track waste"],"about":"Supply continuity at best cost."},
    "cx_lead":{"title":"Customer Experience Lead","cat":"CX","skills":["Support","NPS/CSAT","Playbooks"],"tools":["Intercom","HelpScout","Zendesk"],
             "tasks":["Set up inbox","Macros/playbooks","NPS program","Refund handling"],"about":"Owns voice of customer & loyalty."},
    "data_analyst":{"title":"Data Analyst","cat":"Data","skills":["SQL","Dashboards","Forecasting"],"tools":["BigQuery","Metabase","Sheets"],
             "tasks":["KPI dashboards","Cohorts/retention","Promo analysis","Demand forecast"],"about":"Turns data into decisions."},
    "data_engineer":{"title":"Data Engineer","cat":"Data","skills":["ETL","Connectors","Modeling"],"tools":["Airbyte","DBT","BigQuery"],
             "tasks":["Pipelines","Schema design","Quality checks","CDC sync"],"about":"Builds reliable data foundations."},
    "qa_automation":{"title":"QA Automation","cat":"Engineering","skills":["E2E tests","Monitoring","Alerting"],"tools":["Playwright","Postman","PagerDuty"],
             "tasks":["Checkout tests","Endpoint monitors","SLOs & alerts","Uptime reports"],"about":"Prevents silent failures."},
    "security":{"title":"Security & Compliance","cat":"Engineering","skills":["Access control","PII hygiene","Vendor risk"],"tools":["SSO/OAuth","1Password","DLP"],
             "tasks":["Harden access","Vendor reviews","Retention rules","Phishing drills"],"about":"Reduces risk & protects data."},
    "web_ops_engineer":{"title":"Web Ops Engineer (Res/Order)","cat":"Engineering","skills":["CI/CD","Perf/SEO","Observability"],"tools":["Vercel/Netlify","Lighthouse","Sentry"],
             "tasks":["CI/CD for sites","Page speed/SEO","Error tracking","Blue/green rollouts"],"about":"Keeps sites fast & stable."},
    # People & Legal
    "hr_manager":{"title":"HR Manager","cat":"People","skills":["Hiring","Onboarding","Policies"],"tools":["BambooHR","Notion"],
             "tasks":["Job reqs","Interviews","Onboarding packets","Schedules"],"about":"Builds teams and culture."},
    "legal_compliance":{"title":"Legal & Compliance","cat":"People","skills":["Contracts","Permits","Checklists"],"tools":["Doc templates","E-sign"],
             "tasks":["Vendor MSAs","Food safety docs","Privacy notices","Policy updates"],"about":"Keeps operations compliant."},
}

DEFAULT_ROLE_KEYS = [
    "ops_manager","reservations","reservation_site_manager","booking_integration_engineer",
    "ordering_platform_manager","online_ordering","pos_integration_engineer","delivery_ops","menu",
    "ads","seo_sem_specialist","content","email_crm","social",
    "finance","procurement","cx_lead","data_analyst","data_engineer","qa_automation","security","web_ops_engineer",
    "hr_manager","legal_compliance"
]

def make_agent(role_key: str) -> Dict:
    role = ROLE_LIBRARY[role_key]
    name = fake_name(); email = f"{name.lower().replace(' ','.')}@{AGENT_EMAIL_DOMAIN}"
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
        "about": role["about"], "avatar": avatar,
    }

# ==========================
# Planner → Workflow (DAG)
# ==========================
TEMPLATES: Dict[str, Dict] = {
    # minimal task templates (ids populated at compile time)
    "wf_reservations_boost": {
        "name": "Reservations Conversion Boost",
        "tasks": [
            {"title":"Audit Reservation Widget","owner":"reservation_site_manager","depends_on":[]},
            {"title":"A/B Test CTA & Copy","owner":"reservation_site_manager","depends_on":["Audit Reservation Widget"]},
            {"title":"Connect Confirmation SMS","owner":"booking_integration_engineer","depends_on":["Audit Reservation Widget"]},
            {"title":"Calendar Sync & Blackouts","owner":"booking_integration_engineer","depends_on":["Audit Reservation Widget"]},
            {"title":"Publish & Monitor","owner":"reservations","depends_on":["A/B Test CTA & Copy","Connect Confirmation SMS","Calendar Sync & Blackouts"]},
        ]
    },
    "wf_ordering_launch": {
        "name":"Online Ordering Launch",
        "tasks":[
            {"title":"Map POS Catalog","owner":"pos_integration_engineer","depends_on":[]},
            {"title":"Build Online Menu","owner":"menu","depends_on":["Map POS Catalog"]},
            {"title":"Checkout Flow QA","owner":"qa_automation","depends_on":["Build Online Menu"]},
            {"title":"Payment Callbacks Hardening","owner":"pos_integration_engineer","depends_on":["Build Online Menu"]},
            {"title":"Delivery Zones & Fees","owner":"delivery_ops","depends_on":["Build Online Menu"]},
            {"title":"Go-Live & Observability","owner":"web_ops_engineer","depends_on":["Checkout Flow QA","Payment Callbacks Hardening","Delivery Zones & Fees"]},
        ]
    },
    "wf_growth_marketing": {
        "name":"Full-Funnel Marketing",
        "tasks":[
            {"title":"Keyword & Local SEO Plan","owner":"seo_sem_specialist","depends_on":[]},
            {"title":"Create Launch Creatives","owner":"content","depends_on":["Keyword & Local SEO Plan"]},
            {"title":"Set Up Campaigns","owner":"ads","depends_on":["Create Launch Creatives"]},
            {"title":"Lifecycle Flows (Welcome, Winback)","owner":"email_crm","depends_on":["Set Up Campaigns"]},
            {"title":"Attribution & KPI Dashboard","owner":"data_analyst","depends_on":["Set Up Campaigns"]},
        ]
    },
    "wf_hr_hiring": {
        "name":"Hire & Onboard Staff",
        "tasks":[
            {"title":"Open Job Requisition","owner":"hr_manager","depends_on":[]},
            {"title":"Schedule Interviews","owner":"hr_manager","depends_on":["Open Job Requisition"]},
            {"title":"Offer & Docs","owner":"legal_compliance","depends_on":["Schedule Interviews"]},
            {"title":"Onboarding Packet","owner":"hr_manager","depends_on":["Offer & Docs"]},
        ]
    },
    "wf_inventory_setup": {
        "name":"Inventory & Vendors Setup",
        "tasks":[
            {"title":"Create Vendor List","owner":"procurement","depends_on":[]},
            {"title":"Define Reorder Points","owner":"procurement","depends_on":["Create Vendor List"]},
            {"title":"Connect Vendor Portals","owner":"procurement","depends_on":["Create Vendor List"]},
            {"title":"Stock Initial Inventory","owner":"ops_manager","depends_on":["Define Reorder Points"]},
        ]
    }
}

def infer_intents(txt: str) -> List[str]:
    t = txt.lower()
    intents = []
    if any(k in t for k in ["reservation","booking"]): intents.append("wf_reservations_boost")
    if any(k in t for k in ["order","checkout","delivery","menu","pos"]): intents.append("wf_ordering_launch")
    if any(k in t for k in ["ads","marketing","campaign","seo","sem","email","crm","loyalty"]): intents.append("wf_growth_marketing")
    if any(k in t for k in ["hire","onboard","hr","staff"]): intents.append("wf_hr_hiring")
    if any(k in t for k in ["inventory","vendor","procure","stock"]): intents.append("wf_inventory_setup")
    if not intents: intents = ["wf_ordering_launch","wf_reservations_boost"]
    return intents

def compile_workflow_from_needs(needs_text: str, agents: List[Dict]) -> str:
    intents = infer_intents(needs_text)
    wf_id = f"WF-{int(datetime.utcnow().timestamp())}"
    tasks_map = {}
    for tpl_key in intents:
        tpl = TEMPLATES[tpl_key]
        for item in tpl["tasks"]:
            # resolve owner agent id by role match; pick first
            owner = next((a["id"] for a in agents if a["role_key"] == item["owner"]), None)
            if not owner:  # fallback: any agent with same category
                owner = next((a["id"] for a in agents if a["cat"] == ROLE_LIBRARY[item["owner"]]["cat"]), agents[0]["id"])
            tid = f"T{len(st.session_state.execution)+1:04}"
            tasks_map[item["title"]] = tid
            st.session_state.execution[tid] = {
                "id": tid, "title": item["title"], "owner": owner,
                "status": "Planned", "progress": 0, "depends_on": item["depends_on"][:]
            }
    # convert depends_on names to ids
    for t in st.session_state.execution.values():
        t["depends_on"] = [tasks_map[name] for name in t["depends_on"] if name in tasks_map]
    st.session_state.workflows[wf_id] = {
        "name": " + ".join([TEMPLATES[k]["name"] for k in intents]),
        "task_ids": list(tasks_map.values())
    }
    create_alert("info", f"Compiled workflow: {st.session_state.workflows[wf_id]['name']}")
    return wf_id

# =======================
# Timeline (Gantt)
# =======================
def build_timeline_from_execution() -> pd.DataFrame:
    rows = []
    start = datetime.today().date()
    for t in st.session_state.execution.values():
        idx = int(t["id"][1:])
        week = (idx % 4) + 1
        sd = start + timedelta(days=(week-1)*7 + random.randint(0,2))
        ed = sd + timedelta(days=2 + random.randint(0,2))
        ag = next((a for a in st.session_state.agents if a["id"] == t["owner"]), None)
        rows.append({"Agent": ag["name"] if ag else "Agent", "Role": ag["title"] if ag else "Role",
                     "Task": t["title"], "Start": pd.to_datetime(sd), "End": pd.to_datetime(ed), "Week": week})
    df = pd.DataFrame(rows)
    st.session_state.timeline_df = df.sort_values(["Start","Agent","Task"]).reset_index(drop=True)

def gantt_chart(df: pd.DataFrame):
    if df.empty:
        st.info("Timeline is empty."); return
    chart = alt.Chart(df).mark_bar().encode(
        x="Start:T", x2="End:T", y=alt.Y("Agent:N", sort="-x"),
        color=alt.Color("Week:N", legend=None),
        tooltip=["Agent","Role","Task","Start","End","Week"]
    ).properties(height=480)
    st.altair_chart(chart, use_container_width=True)

# =======================
# Execution State Machine
# =======================
def task_stage(pct: int) -> str:
    if pct >= 100: return "Done"
    if pct >= 70:  return "Review"
    if pct >= 35:  return "In Progress"
    return "Planned"

def exec_tick(n=1):
    ex = st.session_state.execution
    for _ in range(n):
        # move Planned → In Progress if deps done
        for t in ex.values():
            if t["status"] == "Planned" and all(ex[d]["status"] == "Done" for d in t["depends_on"]):
                t["status"] = "In Progress"
        # progress work
        for t in ex.values():
            if t["status"] == "In Progress":
                t["progress"] = min(100, t["progress"] + random.randint(8,16))
                t["status"] = task_stage(t["progress"])
            elif t["status"] == "Review":
                # auto-approve (demo)
                t["status"] = "Done"; t["progress"] = 100

def kanban_snapshot():
    ex = st.session_state.execution
    stages = {"Planned":[], "In Progress":[], "Review":[], "Done":[]}
    for t in ex.values(): stages[t["status"]].append((t["id"], t["title"], t["progress"]))
    return stages

# =======================
# Alerts / Audit
# =======================
def create_alert(level: str, text: str):
    st.session_state.alerts.append({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": level, "text": text})
    # trim
    if len(st.session_state.alerts) > 200:
        st.session_state.alerts = st.session_state.alerts[-200:]

# =======================
# KPIs
# =======================
def compute_kpis() -> Dict[str,str]:
    ex = st.session_state.execution
    if not ex: return {"Tasks Completed":"0/0 (0%)","Orders Today":"0","On-Time Delivery":"—","Campaign ROI":"—","Revenue":"$0","LTV":"—","Active Locs":"0"}
    total = len(ex); done = sum(1 for t in ex.values() if t["status"]=="Done")
    pct = int(done/total*100)
    orders = 120 + done*3 + random.randint(-8,12)
    on_time = min(99, 90 + done//3)
    roi = round(2.2 + done*0.02, 2)
    revenue = 3500 + done*75
    ltv = 84 + done*0.8
    active_locs = len(st.session_state.locations)
    return {"Tasks Completed":f"{done}/{total} ({pct}%)","Orders Today":str(max(0,orders)),
            "On-Time Delivery":f"{on_time}%","Campaign ROI":f"{roi}x","Revenue":f"${int(revenue):,}","LTV":f"${int(ltv)}","Active Locs":str(active_locs)}

def sparkline(values, title):
    df = pd.DataFrame({"x": list(range(len(values))), "y": values})
    ch = alt.Chart(df).mark_line(point=False).encode(x="x:Q", y="y:Q").properties(height=60)
    st.caption(title); st.altair_chart(ch, use_container_width=True)

# =======================
# Updates / Chat / Meetings
# =======================
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

def build_ics(agent_name: str, title: str, start_dt: datetime, duration_min: int, notes: str) -> str:
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_dt.strftime("%Y%m%dT%H%M%SZ")
    dtend   = (start_dt + timedelta(minutes=duration_min)).strftime("%Y%m%dT%H%M%SZ")
    uid = f"{random.randint(100000,999999)}@operai.ai"
    description = notes.replace("\n","\\n")
    return f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//OperAI//Calendar 1.0//EN\nBEGIN:VEVENT\nUID:{uid}\nDTSTAMP:{dtstamp}\nDTSTART:{dtstart}\nDTEND:{dtend}\nSUMMARY:{title or ('Meeting with '+agent_name)}\nDESCRIPTION:{description}\nEND:VEVENT\nEND:VCALENDAR\n"

# =======================
# Helpers: UI + Filters + Assign
# =======================
def jump_to(page: str):
    st.session_state.nav = page
    st.session_state.nav_radio = page

def jump_to_comms(agent_id: str, tab: str):
    st.session_state.comms_target_agent = agent_id
    jump_to("6) Comms")

def top_filters():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([3,2,2,2,2])
    st.session_state.q = c1.text_input("Search roles or skills", value=st.session_state.get("q",""))
    cats = sorted({v["cat"] for v in ROLE_LIBRARY.values()})
    st.session_state.pick = c2.multiselect("Filter by category", options=cats, default=st.session_state.get("pick",[]))
    st.session_state.fav_only = c3.checkbox("Favorites only ★", value=st.session_state.get("fav_only", False))
    if c4.button("⬇️ Download Team JSON"):
        data = serialize_state()
        st.download_button("Download", data=json.dumps(data, indent=2), file_name="operai_state.json", mime="application/json")
    uploaded = c5.file_uploader("Load state (.json)", type=["json"], label_visibility="collapsed")
    if uploaded:
        load_state(json.loads(uploaded.read()))
        st.success("State loaded.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def filtered_agents():
    ags = st.session_state.agents or []
    q = st.session_state.get("q","").lower()
    if q:
        ags = [a for a in ags if q in a["title"].lower() or any(q in s.lower() for s in a["skills"]) or q in a["cat"].lower()]
    picks = st.session_state.get("pick",[])
    if picks: ags = [a for a in ags if a["cat"] in picks]
    if st.session_state.get("fav_only"): ags = [a for a in ags if a["id"] in st.session_state.favorites]
    return ags

def assign_task(owner_id: str, title: str):
    tid = f"T{len(st.session_state.execution)+1:04}"
    st.session_state.execution[tid] = {"id":tid, "title":title.strip(), "owner":owner_id, "status":"Planned", "progress":0, "depends_on":[]}
    create_alert("info", f"Task created: {title}")

def agent_card(ag: Dict):
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        top = st.columns([1,3,1])
        with top[0]:
            st.image(ag["avatar"], caption=ag["name"], use_container_width=True)
        with top[1]:
            st.subheader(ag["title"]); st.markdown(f'<span class="badge">{ag["cat"]}</span>', unsafe_allow_html=True)
            st.write(ag["about"])
            st.markdown('<div class="chips">', unsafe_allow_html=True)
            for s in ag["skills"][:5]: st.markdown(f'<span class="chip">{s}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.expander("Responsibilities (Initial Plan)"):
                for t in ag["tasks"]: st.write(f"• {t}")
            with st.expander("Quick Actions"):
                nt = st.text_input(f"Assign a task to {ag['name']}", key=f"nt_{ag['id']}")
                colqa1, colqa2 = st.columns(2)
                if colqa1.button("Create Task", key=f"cta_{ag['id']}") and nt.strip():
                    assign_task(ag["id"], nt); st.success("Task created and scheduled.")
                play = colqa2.selectbox("Run a playbook", ["—","Reservations Conversion Boost","Ordering Funnel Audit","Weekly P&L Close","Loyalty Winbacks"], key=f"pb_{ag['id']}")
                if colqa2.button("Run Playbook", key=f"pb_run_{ag['id']}") and play!="—":
                    st.info(f"Playbook '{play}' queued (demo).")
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
            record_agent_update(ag["id"]); st.toast(f"Latest update from {ag['name']}")
        upd = st.session_state.last_updates.get(ag["id"]); 
        if upd: st.caption(f"**Latest Update:** {upd}")
        st.markdown('</div>', unsafe_allow_html=True)

# =========
# Persistence (serialize only safe fields)
# =========
SERIALIZE_KEYS = ["founder_name","business_name","business_needs","workflows","execution","last_updates"]
def serialize_state():
    def agent_to_json(a):
        obj = a.copy()
        obj["avatar_b64"] = img_to_b64(a["avatar"])
        obj["avatar"] = None
        return obj
    data = {k: st.session_state.get(k) for k in SERIALIZE_KEYS}
    data["agents"] = [agent_to_json(a) for a in st.session_state.agents]
    data["emails"] = st.session_state.emails
    data["favorites"] = list(st.session_state.favorites)
    # tables
    data["menu_items"] = st.session_state.menu_items.to_dict(orient="records")
    data["inventory"] = st.session_state.inventory.to_dict(orient="records")
    data["vendors"] = st.session_state.vendors.to_dict(orient="records")
    data["locations"] = st.session_state.locations.to_dict(orient="records")
    data["employees"] = st.session_state.employees.to_dict(orient="records")
    data["crm_customers"] = st.session_state.crm_customers.to_dict(orient="records")
    data["experiments"] = st.session_state.experiments.to_dict(orient="records")
    data["connectors"] = st.session_state.connectors.to_dict(orient="records")
    data["alerts"] = st.session_state.alerts[-100:]
    return data

def load_state(data: Dict):
    st.session_state.founder_name = data.get("founder_name","")
    st.session_state.business_name = data.get("business_name","")
    st.session_state.business_needs = data.get("business_needs","")
    st.session_state.workflows = data.get("workflows",{})
    st.session_state.execution = data.get("execution",{})
    st.session_state.last_updates = data.get("last_updates",{})
    # agents
    st.session_state.agents = []
    for a in data.get("agents", []):
        img = b64_to_img(a.get("avatar_b64",""))
        a["avatar"] = img
        a.pop("avatar_b64", None)
        st.session_state.agents.append(a)
    # misc
    st.session_state.emails = data.get("emails",{})
    st.session_state.favorites = set(data.get("favorites",[]))
    # tables
    st.session_state.menu_items = pd.DataFrame(data.get("menu_items", []))
    st.session_state.inventory = pd.DataFrame(data.get("inventory", []))
    st.session_state.vendors = pd.DataFrame(data.get("vendors", []))
    st.session_state.locations = pd.DataFrame(data.get("locations", []))
    st.session_state.employees = pd.DataFrame(data.get("employees", []))
    st.session_state.crm_customers = pd.DataFrame(data.get("crm_customers", []))
    st.session_state.experiments = pd.DataFrame(data.get("experiments", []))
    st.session_state.connectors = pd.DataFrame(data.get("connectors", []))
    st.session_state.alerts = data.get("alerts", [])

# =========
# Banner
# =========
st.markdown("""
<div class="operai-banner">
  <h2 style="margin:0;">🤖 OperAI — The AI Virtual Company</h2>
  <div class="muted" style="margin-top:6px;">Autonomous agents for reservations, ordering, growth, and operations — coordinated, measurable, and always-on.</div>
  <div class="qa">
    <button onclick="window.location.href='#qa-generate'">Generate Team</button>
    <button onclick="window.location.href='#qa-timeline'">Timeline</button>
    <button onclick="window.location.href='#qa-exec'">Task Execution</button>
    <button onclick="window.location.href='#qa-kpi'">KPIs</button>
    <button onclick="window.location.href='#qa-comms'">Comms Hub</button>
    <button onclick="window.location.href='#qa-bos'">Business OS</button>
  </div>
</div>
""", unsafe_allow_html=True)

# =========
# Sidebar
# =========
st.sidebar.title("Navigate")
st.session_state.nav = st.sidebar.radio(
    "",
    ["1) Founder","2) Team","3) Timeline","4) Task Execution","5) KPIs","6) Comms","7) Business OS","8) Alerts & Audit"],
    index=["1) Founder","2) Team","3) Timeline","4) Task Execution","5) KPIs","6) Comms","7) Business OS","8) Alerts & Audit"].index(st.session_state.nav) if st.session_state.get("nav") in ["1) Founder","2) Team","3) Timeline","4) Task Execution","5) KPIs","6) Comms","7) Business OS","8) Alerts & Audit"] else 0,
    key="nav_radio"
)
st.sidebar.markdown("---")
st.sidebar.info("Tip: Pin favorites ★, save/load state, and use per-agent Chat / Meeting / Get Update.")

# =========
# Pages
# =========
# 1) Founder
if st.session_state.nav.startswith("1"):
    st.markdown('<a name="qa-generate"></a>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Founder Input")
        st.write("Describe your business. OperAI will generate a specialized AI team, compile workflows (DAG), and set up execution, KPIs, and modules.")
        c1,c2 = st.columns(2)
        st.session_state.founder_name = c1.text_input("Founder Name", value=st.session_state.founder_name or "Alice Founder")
        st.session_state.business_name = c2.text_input("Business Name", value=st.session_state.business_name or "Aurora Bistro")
        placeholder = textwrap.dedent("""
            I opened a restaurant with two locations and need a reservation site with confirmations and calendar sync,
            an online ordering funnel with POS integration, promos and delivery logistics, lifecycle email/CRM,
            HR hiring & onboarding, inventory & vendor setup, finance close, and security/compliance.
        """).strip()
        st.session_state.business_needs = st.text_area("Business Needs", value=st.session_state.business_needs or placeholder, height=140)
        colg1, colg2, colg3 = st.columns([1,1,1])
        if colg1.button("Generate My AI Team ▶"):
            # build agents
            st.session_state.agents = [make_agent(k) for k in DEFAULT_ROLE_KEYS]
            # compile workflow from needs
            wf_id = compile_workflow_from_needs(st.session_state.business_needs, st.session_state.agents)
            build_timeline_from_execution()
            st.success(f"Team ready. Planned workflow: {st.session_state.workflows[wf_id]['name']}")
        if colg2.button("Add HR + Inventory Workflows"):
            for wf_key in ["wf_hr_hiring","wf_inventory_setup"]:
                _ = compile_workflow_from_needs(wf_key, st.session_state.agents)
            build_timeline_from_execution()
            st.success("Added HR & Inventory workflows.")
        if colg3.button("Reset All"):
            for k in list(st.session_state.keys()):
                if k not in ["seed"]: del st.session_state[k]
            ensure_state(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 2) Team
elif st.session_state.nav.startswith("2"):
    st.subheader("Your AI Team — Advanced Profiles")
    if not st.session_state.agents:
        st.warning("No team yet. Go to **Founder** and click **Generate My AI Team**.")
    else:
        top_filters()
        ags = filtered_agents()
        if not ags: st.info("No roles match your filter.")
        else:
            cols = st.columns(2)
            for i, ag in enumerate(ags):
                with cols[i % 2]: agent_card(ag)

# 3) Timeline
elif st.session_state.nav.startswith("3"):
    st.markdown('<a name="qa-timeline"></a>', unsafe_allow_html=True)
    st.subheader("Project Timeline")
    if st.session_state.timeline_df.empty: st.warning("No timeline yet. Generate your team first.")
    else:
        st.caption("4-week roadmap (color by week). Hover for details.")
        gantt_chart(st.session_state.timeline_df)
        with st.expander("Table View"): st.dataframe(st.session_state.timeline_df, use_container_width=True)

# 4) Task Execution
elif st.session_state.nav.startswith("4"):
    st.markdown('<a name="qa-exec"></a>', unsafe_allow_html=True)
    st.subheader("Task Execution")
    if not st.session_state.execution:
        st.warning("Initialize by generating a team (Founder).")
    else:
        stages = kanban_snapshot()
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### Kanban Snapshot")
            st.markdown('<div class="kanban">', unsafe_allow_html=True)
            for name in ["Planned","In Progress","Review","Done"]:
                st.markdown('<div class="kcol">', unsafe_allow_html=True)
                st.markdown(f"<h5>{name} <span class='kcount'>({len(stages[name])})</span></h5>", unsafe_allow_html=True)
                for tid, title, pct in sorted(stages[name], key=lambda x: -x[2])[:8]:
                    st.markdown(f"<div class='kcard'>{title} — <b>{pct}%</b> <span class='small'>({tid})</span></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)

            left, right = st.columns([2,1])
            with left:
                st.caption("Advance cycles to progress tasks.")
                if st.button("Advance 5 Ticks ▶"): exec_tick(5); st.rerun()
                st.markdown("### In-flight Tasks (sample)")
                for tid, t in list(st.session_state.execution.items())[:16]:
                    st.progress(t["progress"], text=f"{t['title']} — {t['progress']}%  ({t['status']})")
            with right:
                st.markdown("### Controls")
                n = st.number_input("Advance N ticks", min_value=1, max_value=300, value=12, step=1)
                if st.button("Advance"): exec_tick(n); st.rerun()
                if st.button("Reset Execution"):
                    for t in st.session_state.execution.values():
                        t["status"]="Planned"; t["progress"]=0
                    st.success("Execution state reset."); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# 5) KPIs
elif st.session_state.nav.startswith("5"):
    st.markdown('<a name="qa-kpi"></a>', unsafe_allow_html=True)
    st.subheader("KPI Dashboard")
    if not st.session_state.execution:
        st.warning("Generate your team and compile a workflow first.")
    else:
        k = compute_kpis()
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
            c1.metric("Tasks Completed", k["Tasks Completed"])
            c2.metric("Orders Today", k["Orders Today"])
            c3.metric("On-Time Delivery", k["On-Time Delivery"])
            c4.metric("Campaign ROI", k["Campaign ROI"])
            c5.metric("Revenue", k["Revenue"])
            c6.metric("Est. LTV", k["LTV"])
            c7.metric("Active Locations", k["Active Locs"])
            st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)
            s1, s2, s3 = st.columns(3)
            with s1: sparkline([random.randint(40,120) for _ in range(14)], "Orders per Hour")
            with s2: sparkline([random.randint(80,98) for _ in range(14)], "On-Time % Trend")
            with s3: sparkline([round(1.8 + i*0.03 + random.random()*0.05,2) for i in range(14)], "Campaign ROI Trend")
            st.markdown('</div>', unsafe_allow_html=True)

# 6) Comms
elif st.session_state.nav.startswith("6"):
    st.markdown('<a name="qa-comms"></a>', unsafe_allow_html=True)
    st.subheader("Comms Hub — Contact • Chat • Meetings • Updates")
    if not st.session_state.agents: st.warning("No team yet. Generate your team in Founder.")
    else:
        tabs = st.tabs(["Directory","Chat","Meetings","Latest Updates"])

        with tabs[0]:
            top_filters()
            ags = filtered_agents()
            cols = st.columns(2)
            for i, ag in enumerate(ags):
                with cols[i % 2]: agent_card(ag)

        with tabs[1]:
            names = {a["id"]: f"{a['name']} — {a['title']}" for a in st.session_state.agents}
            target = st.session_state.comms_target_agent or list(names.keys())[0]
            sel = st.selectbox("Choose an agent", options=list(names.keys()),
                index=list(names.keys()).index(target) if target in names else 0,
                format_func=lambda k: names[k])
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"#### Chat with {names[sel]}")
                hist = st.session_state.chats.get(sel, [])
                for msg in hist[-14:]:
                    who = "You" if msg["role"]=="user" else "Agent"
                    st.markdown(f"**{who} ({msg['ts']}):** {msg['text']}")
                user_msg = st.text_input("Type your message", key=f"chat_input_{sel}")
                c1,c2,c3 = st.columns(3)
                if c1.button("Send"):
                    if user_msg.strip():
                        st.session_state.chats[sel].append({"role":"user","text":user_msg.strip(),"ts":str(datetime.now())})
                        reply = random.choice(["Acknowledged. Moving forward.","Coordinating with linked roles.","Pushing change and monitoring.","Starting now."])
                        st.session_state.chats[sel].append({"role":"agent","text":reply,"ts":str(datetime.now())})
                        st.session_state.comms_target_agent = sel; st.rerun()
                if c2.button("Clear Chat"):
                    st.session_state.chats[sel] = [{"role":"agent","text":"Chat reset. How can I help?","ts":str(datetime.now())}]
                    st.rerun()
                if c3.button("🔄 Get Update (this agent)"):
                    record_agent_update(sel); st.toast(f"Latest update pulled from {names[sel]}")
                upd = st.session_state.last_updates.get(sel)
                if upd: st.caption(f"**Latest Update:** {upd}")
                st.markdown('</div>', unsafe_allow_html=True)

        with tabs[2]:
            names = {a["id"]: f"{a['name']} — {a['title']}" for a in st.session_state.agents}
            target = st.session_state.comms_target_agent or list(names.keys())[0]
            sel = st.selectbox("Choose an agent", options=list(names.keys()),
                index=list(names.keys()).index(target) if target in names else 0,
                format_func=lambda k: names[k], key="meet_sel")
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                mt_title = st.text_input("Meeting Title", value="Operational Sync")
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

        with tabs[3]:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Get Latest Updates from All Agents")
                c = st.columns([1,1,2])
                if c[0].button("Get All Updates 🔄"):
                    for ag in st.session_state.agents: record_agent_update(ag["id"])
                    st.success("Updates received.")
                if c[1].button("Clear Updates"):
                    st.session_state.last_updates = {}; st.rerun()
                for ag in st.session_state.agents:
                    upd = st.session_state.last_updates.get(ag["id"], "No update yet.")
                    st.write(f"**{ag['name']} — {ag['title']}**: {upd}")
                st.markdown('</div>', unsafe_allow_html=True)

# 7) Business OS
elif st.session_state.nav.startswith("7"):
    st.markdown('<a name="qa-bos"></a>', unsafe_allow_html=True)
    st.subheader("Business OS")
    bos_tab = st.tabs(["Menu Studio","Reservations Ops","Ordering Ops","Delivery Ops","Finance","Marketing","CX","Inventory","Vendors","Locations","HR","Legal & Compliance","CRM & Loyalty","Experiments","Data Pipes","Settings"])

    # --- Menu Studio ---
    with bos_tab[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Menu Studio — Items")
        st.caption("Manage items, prices, categories, cost, availability, and publish to channels.")
        st.dataframe(st.session_state.menu_items, use_container_width=True)
        with st.expander("Add / Edit Item"):
            col1,col2,col3 = st.columns(3)
            name = col1.text_input("Name")
            category = col2.text_input("Category")
            price = col3.number_input("Price", 0.0, 999.0, 9.99, step=0.5)
            sku = col1.text_input("SKU")
            tags = col2.text_input("Tags (comma)")
            cost = col3.number_input("Unit Cost", 0.0, 999.0, 2.50, step=0.1)
            available = col1.checkbox("Available", value=True)
            if st.button("Add Item"):
                st.session_state.menu_items.loc[len(st.session_state.menu_items)] = {
                    "id": str(uuid.uuid4()), "name": name, "category": category, "price": float(price),
                    "sku": sku, "tags": tags, "img": "", "cost": float(cost), "available": bool(available)
                }
                st.success("Item added.")
        c1,c2,c3,c4 = st.columns(4)
        if c1.button("Run Schema Check"):
            st.info("✓ JSON-LD schema for MenuItem valid (demo).")
        if c2.button("Sync to POS"):
            st.success("POS sync queued (demo).")
        if c3.button("Publish to Channels"):
            st.success("Publishing to: Website, Google, UberEats, DoorDash (demo).")
        if c4.button("Price Optimizer (demo)"):
            st.info("Suggested +$0.50 on top 3 sellers; −$0.25 on low movers.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Reservations Ops ---
    with bos_tab[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Reservations Automation")
        a1,a2 = st.columns(2)
        remind = a1.checkbox("SMS reminder 24h before", value=True)
        noshow = a1.checkbox("No-show winback next day", value=True)
        blackout = a2.text_input("Blackout dates (CSV, YYYY-MM-DD)", value="")
        if st.button("Apply Automations"):
            st.success("Automations saved (demo). Webhook workers will enforce.")
        st.markdown('<hr class="hr-soft"/>', unsafe_allow_html=True)
        st.subheader("Funnel KPIs")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Visits→Widget Open", "62%", "+5%")
        c2.metric("Widget→Confirm", "28%", "+3%")
        c3.metric("No-show Rate", "6.8%", "-1.1%")
        c4.metric("Avg Party Size", "2.7", "+0.1")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Ordering Ops ---
    with bos_tab[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Ordering Health")
        c1,c2,c3 = st.columns(3)
        c1.metric("Checkout Conversion", "42%", "+3%")
        c2.metric("Payment Callback Success", "99.8%", "+0.3%")
        c3.metric("Avg Fulfillment Time", "26m", "-2m")
        if st.button("Run Synthetic Order"):
            st.success("E2E order succeeded in 3.2s (demo).")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Delivery Ops ---
    with bos_tab[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Delivery Logistics")
        c1,c2,c3 = st.columns(3)
        c1.metric("On-Time %", "94%", "+1%")
        c2.metric("Avg ETA Error", "±3m", "-1m")
        c3.metric("Orders Routed", "182", "+12")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Finance ---
    with bos_tab[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Finance & P&L (Demo)")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Revenue (7d)", "$42,380", "+$2,110")
        # compute rough gross margin from menu cost
        if not st.session_state.menu_items.empty:
            rev = st.session_state.menu_items["price"].sum()
            cogs = st.session_state.menu_items["cost"].sum()
            gm = (1 - (cogs / rev)) * 100 if rev>0 else 0
        else:
            gm = 68.0
        c2.metric("Gross Margin % (menu est.)", f"{gm:.1f}%")
        c3.metric("AOV", "$28.40", "+$1.10")
        c4.metric("Cash on Hand", "$83,200", "—")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Marketing ---
    with bos_tab[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Marketing Hub")
        cc1, cc2 = st.columns(2)
        with cc1:
            st.write("Campaigns")
            st.table(pd.DataFrame([
                {"Name":"Launch Q4","Budget/day":"$120","Status":"Active"},
                {"Name":"Reservations Boost","Budget/day":"$80","Status":"Learning"},
                {"Name":"Winback Series (Email)","Budget/day":"—","Status":"Active"},
            ]))
        with cc2:
            st.write("Content Calendar (this week)")
            st.table(pd.DataFrame([
                {"Day":"Mon","Channel":"IG","Post":"Menu teaser"},
                {"Day":"Wed","Channel":"TikTok","Post":"Kitchen BTS Reel"},
                {"Day":"Fri","Channel":"Email","Post":"VIP early access"},
            ]))
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CX ---
    with bos_tab[6]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("CX Desk")
        st.metric("NPS (30d)", "54", "+6")
        st.metric("First Response Time", "7m", "-2m")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Inventory ---
    with bos_tab[7]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Inventory")
        st.dataframe(st.session_state.inventory, use_container_width=True)
        low = st.session_state.inventory[st.session_state.inventory["on_hand"] <= st.session_state.inventory["reorder_point"]]
        if not low.empty:
            st.warning(f"Reorder suggested for: {', '.join(low['sku'].tolist())}")
            if st.button("Generate Reorder Draft (demo)"):
                create_alert("warning","Generated reorder PO draft for low stock SKUs.")
                st.success("PO draft created (demo).")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Vendors ---
    with bos_tab[8]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendors & Terms")
        st.dataframe(st.session_state.vendors, use_container_width=True)
        with st.expander("Add Vendor"):
            v1,v2,v3,v4 = st.columns(4)
            n = v1.text_input("Name")
            c = v2.text_input("Contact Email")
            ld = v3.number_input("Lead Days", 0, 30, 2)
            t = v4.text_input("Payment Terms", "Net 30")
            if st.button("Add Vendor"):
                st.session_state.vendors.loc[len(st.session_state.vendors)] = {"id":str(uuid.uuid4()),"name":n,"contact":c,"lead_days":ld,"terms":t}
                st.success("Vendor added.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Locations ---
    with bos_tab[9]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Locations")
        st.dataframe(st.session_state.locations, use_container_width=True)
        with st.expander("Add Location"):
            l1,l2,l3,l4 = st.columns(4)
            nm = l1.text_input("Name")
            tz = l2.text_input("Timezone", "America/New_York")
            addr = l3.text_input("Address")
            openh = l4.text_input("Open", "11:00")
            closeh = l1.text_input("Close", "22:00")
            if st.button("Add Location"):
                st.session_state.locations.loc[len(st.session_state.locations)] = {
                    "id":str(uuid.uuid4()),"name":nm,"tz":tz,"address":addr,"open":openh,"close":closeh
                }
                st.success("Location added.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HR ---
    with bos_tab[10]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("HR — People")
        st.dataframe(st.session_state.employees, use_container_width=True)
        with st.expander("Add Employee"):
            h1,h2,h3,h4 = st.columns(4)
            nm = h1.text_input("Full Name")
            rl = h2.text_input("Role")
            loc = h3.text_input("Location")
            stt = h4.selectbox("Status", ["Active","Leave","Contract"], index=0)
            if st.button("Add Employee"):
                st.session_state.employees.loc[len(st.session_state.employees)] = {
                    "id":str(uuid.uuid4()),"name":nm,"role":rl,"location":loc,"status":stt
                }
                st.success("Employee added.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Legal & Compliance ---
    with bos_tab[11]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Legal & Compliance")
        st.write("Permits, policy docs, and vendor agreements (demo).")
        c1,c2,c3 = st.columns(3)
        c1.metric("Permits up-to-date", "Yes", "")
        c2.metric("Vendor MSAs", "3", "")
        c3.metric("Open Issues", "0", "")
        if st.button("Run Compliance Checklist"):
            create_alert("info","Compliance checklist run: all green.")
            st.success("Checklist completed. No issues found.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CRM & Loyalty ---
    with bos_tab[12]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("CRM & Loyalty")
        st.dataframe(st.session_state.crm_customers, use_container_width=True)
        with st.expander("Create Segment (demo)"):
            seg = st.text_input("Segment Name", "At-risk (no visit 30d)")
            if st.button("Create Segment"):
                st.success(f"Segment '{seg}' created (demo).")
        with st.expander("Send Campaign (demo)"):
            subj = st.text_input("Subject", "We miss you — dinner on us?")
            if st.button("Send Preview"):
                create_alert("info","Sent preview to founder.")
                st.success("Preview sent (demo).")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Experiments ---
    with bos_tab[13]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Experiments")
        st.dataframe(st.session_state.experiments, use_container_width=True)
        with st.expander("Propose New Experiment"):
            e1,e2,e3 = st.columns(3)
            name = e1.text_input("Name", "Free dessert banner")
            area = e2.selectbox("Area", ["Reservations","Ordering","Delivery","Menu","Pricing","Email/Lifecycle"], index=2)
            metric = e3.text_input("Primary Metric", "Checkout CR")
            if st.button("Add Experiment"):
                st.session_state.experiments.loc[len(st.session_state.experiments)] = {
                    "id":str(uuid.uuid4()),"name":name,"area":area,"status":"Proposed","metric":metric,"uplift_pct":0.0
                }
                st.success("Experiment proposed.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Data Pipes ---
    with bos_tab[14]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Data Pipes & Connectors")
        st.dataframe(st.session_state.connectors, use_container_width=True)
        with st.expander("Connect New (demo)"):
            d1,d2 = st.columns(2)
            nm = d1.text_input("Name")
            tp = d2.text_input("Type")
            if st.button("Connect"):
                st.session_state.connectors.loc[len(st.session_state.connectors)] = {"id":str(uuid.uuid4()),"name":nm,"type":tp,"status":"Connecting"}
                create_alert("info", f"Connecting to {nm}…")
                st.success("Connector initiated (demo).")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Settings ---
    with bos_tab[15]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Settings & Export")
        st.write("Save/Load full OperAI state as a JSON bundle.")
        c1, c2 = st.columns(2)
        if c1.button("Export State (.json)"):
            data = serialize_state()
            st.download_button("Download operai_state.json", data=json.dumps(data, indent=2),
                               file_name="operai_state.json", mime="application/json")
        uploaded = c2.file_uploader("Import State (.json)", type=["json"])
        if uploaded and st.button("Load"):
            load_state(json.loads(uploaded.read()))
            st.success("State loaded."); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 8) Alerts & Audit
elif st.session_state.nav.startswith("8"):
    st.subheader("Alerts & Audit Log")
    if not st.session_state.alerts:
        st.info("No alerts yet. Actions you take will show here.")
    else:
        for a in reversed(st.session_state.alerts[-100:]):
            st.write(f"[{a['ts']}] **{a['level'].upper()}** — {a['text']}")

# Footer
st.markdown('<div class="muted" style="margin-top:14px;">© OperAI — Premium Streamlit Demo</div>', unsafe_allow_html=True)
