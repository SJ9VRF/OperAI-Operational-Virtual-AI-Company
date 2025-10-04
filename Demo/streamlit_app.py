# streamlit_app.py
# OperAI — Interactive Demo (Founder Input → AI Team → Timeline → Simulation → KPIs)
# Run: streamlit run streamlit_app.py

import streamlit as st
import random
import textwrap
import time
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict

# ------------------------------
# Helpers & Session Bootstrap
# ------------------------------
st.set_page_config(page_title="OperAI — Interactive Demo", page_icon="🤖", layout="wide")

def ensure_state():
    ss = st.session_state
    ss.setdefault("founder_name", "")
    ss.setdefault("business_needs", "")
    ss.setdefault("agents", [])
    ss.setdefault("timeline_df", pd.DataFrame())
    ss.setdefault("simulation_progress", {})
    ss.setdefault("kpis", {})
    ss.setdefault("seed", 42)

ensure_state()
random.seed(st.session_state.seed)

# ------------------------------
# Minimal fake role library (extensible)
# ------------------------------
ROLE_LIBRARY: Dict[str, Dict] = {
    "online_ordering": {
        "title": "Online Ordering Manager",
        "skills": ["POS integration", "Menu sync", "Order routing"],
        "tools": ["Square/Toast", "Shopify", "Zapier"],
        "tasks": [
            "Connect POS & payments",
            "Publish online menu",
            "Setup order notifications",
            "QA test checkout flow",
        ],
    },
    "delivery_ops": {
        "title": "Delivery Coordinator",
        "skills": ["Dispatch", "Routing", "SLA tracking"],
        "tools": ["UberEats", "DoorDash", "Google Maps API"],
        "tasks": [
            "Integrate delivery partners",
            "Configure delivery zones",
            "Set fees & promos",
            "Monitor on-time rate",
        ],
    },
    "ads": {
        "title": "Ad Campaign Specialist",
        "skills": ["Targeting", "Budgeting", "Attribution"],
        "tools": ["Meta Ads", "Google Ads", "GA4"],
        "tasks": [
            "Define audiences",
            "Launch campaigns",
            "A/B test creatives",
            "Optimize ROAS",
        ],
    },
    "content": {
        "title": "Content Creator",
        "skills": ["Copywriting", "Design", "Brand voice"],
        "tools": ["Canva", "Figma", "CapCut"],
        "tasks": [
            "Create promo images",
            "Write ad copy",
            "Design menu highlights",
            "Schedule social posts",
        ],
    },
    "social": {
        "title": "Social Media Manager",
        "skills": ["Community", "Scheduling", "Analytics"],
        "tools": ["Instagram", "TikTok", "Buffer"],
        "tasks": [
            "Plan weekly calendar",
            "Publish daily posts",
            "Reply to DMs",
            "Track engagement",
        ],
    },
    "reservations": {
        "title": "Reservation Agent",
        "skills": ["Table mgmt", "CRM", "Email/SMS"],
        "tools": ["OpenTable", "Resy", "Twilio"],
        "tasks": [
            "Integrate booking widget",
            "Set seating rules",
            "Confirm bookings",
            "Analyze no-shows",
        ],
    },
    "menu": {
        "title": "Menu Manager",
        "skills": ["Categorization", "Pricing", "Nutrition"],
        "tools": ["Google Sheets", "POS Menu Editor"],
        "tasks": [
            "Structure categories",
            "Upload items & prices",
            "Add images & tags",
            "Sync channels",
        ],
    },
    "finance": {
        "title": "Accountant",
        "skills": ["Invoicing", "P&L", "Cash flow"],
        "tools": ["QuickBooks", "Stripe", "Xero"],
        "tasks": [
            "Connect bank & gateway",
            "Set up chart of accounts",
            "Weekly P&L draft",
            "Cash flow forecast",
        ],
    },
    "procurement": {
        "title": "Procurement Officer",
        "skills": ["Vendors", "Inventory", "Cost control"],
        "tools": ["Sheets", "Email", "Vendor Portals"],
        "tasks": [
            "List suppliers",
            "Negotiate prices",
            "Set reorder points",
            "Track spoilage",
        ],
    },
}

KEYWORD_TO_ROLES = {
    "online ordering": ["online_ordering", "menu"],
    "ordering": ["online_ordering", "menu"],
    "delivery": ["delivery_ops"],
    "deliveries": ["delivery_ops"],
    "ads": ["ads", "content", "social"],
    "advertising": ["ads", "content", "social"],
    "campaign": ["ads", "content"],
    "content": ["content", "social"],
    "social": ["social", "content"],
    "reservation": ["reservations"],
    "reservations": ["reservations"],
    "menu": ["menu"],
    "accounting": ["finance"],
    "finance": ["finance"],
    "procurement": ["procurement"],
    "supply": ["procurement"],
    "supply chain": ["procurement"],
    "inventory": ["procurement"],
    "receipt": ["finance"],
}

DEFAULT_ROLE_KEYS_FOR_RESTAURANT = [
    "online_ordering",
    "delivery_ops",
    "ads",
    "content",
    "social",
    "reservations",
    "menu",
    "finance",
    "procurement",
]

# ------------------------------
# Profile image generator (initials bubble)
# ------------------------------
def initials_avatar(name: str, size: int = 160) -> Image.Image:
    colors = ["#4B8BF4", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6", "#06B6D4"]
    bg = random.choice(colors)
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    initials = "".join([p[0] for p in name.split()[:2]]).upper() or "AI"
    # Try to find a nice font size
    font_size = int(size * 0.45)
    try:
        # Common macOS path; if missing, PIL will fall back below
        font = ImageFont.truetype("Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    w, h = draw.textbbox((0,0), initials, font=font)[2:]
    draw.text(((size - w) / 2, (size - h) / 2 - 6), initials, fill="white", font=font)
    return img

def fake_name():
    first = random.choice(
        ["Sophia","Liam","Olivia","Noah","Ava","Ethan","Mia","Lucas","Isabella","Leo","Amelia","Mason","Chloe","Aiden","Zoe","Aria","Ella","Luna","Nora","Kai"]
    )
    last = random.choice(
        ["Lopez","Kim","Patel","Rodriguez","Nguyen","Smith","Chen","Garcia","Singh","Brown","Khan","Hernandez","Wang","Davis","Martinez","Wilson","Anderson","Clark"]
    )
    return f"{first} {last}"

# ------------------------------
# Mapping needs → roles
# ------------------------------
def extract_roles_from_needs(needs: str) -> List[str]:
    needs_lc = needs.lower()
    selected = set()
    for k, roles in KEYWORD_TO_ROLES.items():
        if k in needs_lc:
            selected.update(roles)
    # Fallback: if nothing matched, assume restaurant starter pack
    if not selected:
        selected.update(DEFAULT_ROLE_KEYS_FOR_RESTAURANT)
    return list(selected)

def make_agent(role_key: str) -> Dict:
    role = ROLE_LIBRARY[role_key]
    name = fake_name()
    img = initials_avatar(name, 160)
    # Convert PIL image to bytes for st.image (so we can keep in memory)
    return {
        "id": f"{role_key}-{random.randint(1000,9999)}",
        "name": name,
        "role_key": role_key,
        "title": role["title"],
        "skills": role["skills"],
        "tools": role["tools"],
        "tasks": role["tasks"],
        "avatar": img,
    }

def generate_team(needs: str) -> List[Dict]:
    role_keys = extract_roles_from_needs(needs)
    return [make_agent(k) for k in role_keys]

# ------------------------------
# Timeline (simple 4-week roadmap)
# ------------------------------
def build_timeline(agents: List[Dict]) -> pd.DataFrame:
    start = datetime.today().date()
    rows = []
    for idx, ag in enumerate(agents):
        for t_idx, task in enumerate(ag["tasks"]):
            # Spread tasks across 4 weeks
            week = (t_idx % 4) + 1
            start_date = start + timedelta(days=(week-1)*7 + random.randint(0,2))
            end_date = start_date + timedelta(days=2 + random.randint(0,2))
            rows.append({
                "Agent": ag["name"],
                "Role": ag["title"],
                "Task": task,
                "Start": pd.to_datetime(start_date),
                "End": pd.to_datetime(end_date),
                "Week": week
            })
    df = pd.DataFrame(rows)
    return df.sort_values(["Start","Agent","Task"]).reset_index(drop=True)

def gantt_chart(df: pd.DataFrame):
    if df.empty:
        st.info("Timeline is empty.")
        return
    chart = alt.Chart(df).mark_bar().encode(
        x="Start:T",
        x2="End:T",
        y=alt.Y("Agent:N", sort="-x"),
        color="Week:N",
        tooltip=["Agent","Role","Task","Start","End","Week"]
    ).properties(height=420)
    st.altair_chart(chart, use_container_width=True)

# ------------------------------
# Simulation
# ------------------------------
def initialize_simulation(df: pd.DataFrame):
    prog = {}
    for _, row in df.iterrows():
        task_id = f"{row.Agent}:{row.Task}"
        prog[task_id] = random.randint(0, 15)  # initial state
    st.session_state.simulation_progress = prog

def step_simulation(step: int = 10):
    prog = st.session_state.simulation_progress
    for k in list(prog.keys()):
        # Simple dependency heuristic: tasks in Week N wait a bit on Week N-1 of same agent
        agent, task = k.split(":", 1)
        inc = random.randint(3, 12)
        prog[k] = min(100, prog[k] + inc)
    st.session_state.simulation_progress = prog

# ------------------------------
# KPI calculation (fake live metrics)
# ------------------------------
def compute_kpis(progress: Dict[str, int], agents: List[Dict]) -> Dict:
    total_tasks = len(progress)
    done = sum(1 for v in progress.values() if v >= 100)
    pct = int((done / total_tasks) * 100) if total_tasks else 0

    orders = 120 + done * 3 + random.randint(-8, 12)
    on_time_rate = 90 + min(9, done // 3)
    roi = 2.2 + (done * 0.02)
    revenue = 3500 + done * 75

    # Role-aware bumps
    role_titles = {a["title"] for a in agents}
    if "Ad Campaign Specialist" in role_titles:
        roi += 0.2
    if "Delivery Coordinator" in role_titles:
        on_time_rate += 1
    if "Accountant" in role_titles:
        revenue += 150

    return {
        "Tasks Completed": f"{done}/{total_tasks} ({pct}%)",
        "Orders Today": max(0, orders),
        "Delivery On-Time %": f"{min(99, on_time_rate)}%",
        "Campaign ROI (x)": round(roi, 2),
        "Revenue (USD)": f"${int(revenue):,}"
    }

# ------------------------------
# UI — Sidebar Navigation
# ------------------------------
st.sidebar.title("OperAI — Demo")
page = st.sidebar.radio(
    "Navigate",
    ["1) Founder Input", "2) AI Team", "3) Timeline", "4) Run Simulation", "5) KPI Dashboard"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("Operate Smarter, Grow Faster 🚀")

# ------------------------------
# Page 1 — Founder Input
# ------------------------------
if page.startswith("1"):
    st.title("Founder Input")
    st.write("Describe your business and needs. OperAI will generate a virtual AI team, a timeline, and a live KPI dashboard.")

    st.session_state.founder_name = st.text_input("Founder Name", value=st.session_state.founder_name or "Alice Founder")
    placeholder = textwrap.dedent("""
        I opened a restaurant and need online ordering, delivery setup, advertising campaigns,
        content creation, reservation management, menu structuring, accounting, and procurement.
    """).strip()
    st.session_state.business_needs = st.text_area(
        "Business Needs",
        value=st.session_state.business_needs or placeholder,
        height=140
    )

    if st.button("Generate My AI Team", type="primary"):
        st.session_state.agents = generate_team(st.session_state.business_needs)
        st.session_state.timeline_df = build_timeline(st.session_state.agents)
        initialize_simulation(st.session_state.timeline_df)
        st.success("Your AI team, timeline, and simulation are ready! Navigate to **AI Team** → **Timeline** → **Run Simulation** → **KPI Dashboard**.")

# ------------------------------
# Page 2 — AI Team
# ------------------------------
elif page.startswith("2"):
    st.title("Your AI Team")
    if not st.session_state.agents:
        st.warning("No team yet. Go to **Founder Input** and click **Generate My AI Team**.")
    else:
        cols = st.columns(3)
        for i, ag in enumerate(st.session_state.agents):
            with cols[i % 3]:
                st.image(ag["avatar"], caption=ag["name"], use_container_width=True)
                st.subheader(ag["title"])
                st.markdown(f"**Skills:** {', '.join(ag['skills'])}")
                st.markdown(f"**Tools:** {', '.join(ag['tools'])}")
                with st.expander("Planned Tasks"):
                    for t in ag["tasks"]:
                        st.write(f"• {t}")

# ------------------------------
# Page 3 — Timeline
# ------------------------------
elif page.startswith("3"):
    st.title("Project Timeline")
    if st.session_state.timeline_df.empty:
        st.warning("No timeline yet. Generate your team first.")
    else:
        st.caption("4-week roadmap (color by week). Hover for details.")
        gantt_chart(st.session_state.timeline_df)
        with st.expander("Table View"):
            st.dataframe(st.session_state.timeline_df, use_container_width=True)

# ------------------------------
# Page 4 — Run Simulation
# ------------------------------
elif page.startswith("4"):
    st.title("Execution Simulation")
    if not st.session_state.simulation_progress:
        st.warning("Initialize the simulation by generating a team and timeline.")
    else:
        left, right = st.columns([2,1])
        with left:
            st.caption("Press **Advance 5 seconds** a few times to watch tasks progress like a real team at work.")
            if st.button("Advance 5 seconds ▶️", type="primary"):
                # Simulate 5 'ticks'
                for _ in range(5):
                    step_simulation()
                st.rerun()

            st.markdown("### Task Progress")
            # Show a sample of up to 12 tasks to keep UI snappy
            sample_items = list(st.session_state.simulation_progress.items())[:12]
            for task_id, pct in sample_items:
                st.progress(pct, text=f"{task_id} — {pct}%")

        with right:
            st.markdown("### Simulation Controls")
            tick_n = st.number_input("Manual ticks", min_value=1, max_value=100, value=10, step=1)
            if st.button("Advance N ticks"):
                for _ in range(tick_n):
                    step_simulation()
                st.rerun()

            if st.button("Reset Simulation"):
                initialize_simulation(st.session_state.timeline_df)
                st.success("Simulation reset.")
                st.rerun()

# ------------------------------
# Page 5 — KPI Dashboard
# ------------------------------
elif page.startswith("5"):
    st.title("KPI Dashboard")
    if not st.session_state.agents or not st.session_state.simulation_progress:
        st.warning("Generate your team and run the simulation first.")
    else:
        st.caption("Live metrics derived from current task completion (demo).")
        st.session_state.kpis = compute_kpis(st.session_state.simulation_progress, st.session_state.agents)

        k = st.session_state.kpis
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tasks Completed", k["Tasks Completed"])
        c2.metric("Orders Today", k["Orders Today"])
        c3.metric("On-Time Delivery", k["Delivery On-Time %"])
        c4.metric("Campaign ROI", f"{k['Campaign ROI (x)']}x")
        c5.metric("Revenue", k["Revenue (USD)"])

        st.markdown("---")
        st.subheader("Agent Activity (Transparent Logs)")
        for ag in st.session_state.agents[:6]:
            # lightweight, playful status line
            status = random.choice([
                "Waiting for content approval…",
                "Publishing campaign updates…",
                "Syncing menu to POS…",
                "Confirming reservations…",
                "Reconciling payouts…",
                "Negotiating supplier terms…",
                "Optimizing delivery zones…",
            ])
            st.write(f"**{ag['name']} — {ag['title']}**: {status}")
