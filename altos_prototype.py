import streamlit as st
import requests
import json
import re
import os

st.set_page_config(
    page_title="AltOS — Process Intelligence",
    page_icon="⚙️",
    layout="wide",
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .block-container { padding-top: 2rem; }
    h1 { color: #e2e8f0; font-size: 2.2rem; font-weight: 700; }
    h2 { color: #cbd5e1; font-size: 1.4rem; font-weight: 600; margin-top: 1.5rem; }
    h3 { color: #94a3b8; font-size: 1.1rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: 600; color: #94a3b8; }
    .stTabs [aria-selected="true"] { color: #38bdf8; border-bottom: 2px solid #38bdf8; }
    .card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .card-step { border-left: 4px solid #38bdf8; }
    .card-auto { border-left: 4px solid #34d399; }
    .card-decision { border-left: 4px solid #f59e0b; }
    .card-bottleneck { border-left: 4px solid #f87171; }
    .card-suggestion { border-left: 4px solid #34d399; }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .badge-step { background: #0c4a6e; color: #38bdf8; }
    .badge-auto { background: #064e3b; color: #34d399; }
    .badge-decision { background: #451a03; color: #f59e0b; }
    .badge-bottleneck { background: #450a0a; color: #f87171; }
    .badge-suggestion { background: #064e3b; color: #34d399; }
    .score-ring {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
    }
    .score-label { text-align: center; color: #94a3b8; font-size: 0.9rem; margin-top: -0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Gemini client ────────────────────────────────────────────────────────────
def call_claude(prompt: str, system: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": prompt}]}],
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        st.error(f"API error: {e}")
        return ""


def parse_json_block(text: str) -> dict | list | None:
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    raw = match.group(1) if match else text
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return None


# ── Sidebar — API Key ────────────────────────────────────────────────────────
st.caption("Built with Gemini 2.0 Flash · Streamlit")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# ⚙️ AltOS — Process Intelligence Platform")
st.caption("Design scalable operations · Eliminate bottlenecks · Automate intelligently")
st.markdown("---")

tab1, tab2 = st.tabs(["🗺️ Process Architect", "📊 Client Operations Optimizer"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Process Architect (mini AltOS)
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Process Architect")
    st.caption("Input any business process and get a structured breakdown — steps, automations, and decision points.")

    col1, col2 = st.columns([2, 1])
    with col1:
        process_input = st.text_area(
            "Describe the process",
            placeholder="e.g. Onboarding a new B2B client for a SaaS product",
            height=100,
        )
    with col2:
        team_size = st.selectbox("Team size", ["Solo / 1-2", "Small (3-10)", "Medium (11-50)", "Large (50+)"])
        industry = st.selectbox("Industry", ["SaaS / Tech", "Consulting", "E-commerce", "Finance", "Healthcare", "Other"])

    analyze_btn = st.button("Analyze Process →", type="primary", use_container_width=True)

    if analyze_btn and process_input.strip():
        SYSTEM = """You are an expert in business process design and operations.
You think in systems: every process has steps, automation opportunities, and decision gates.
Always respond with valid JSON only — no prose, no markdown outside the JSON block."""

        PROMPT = f"""Analyze this business process and return a JSON object with exactly this structure:

Process: "{process_input}"
Context: Team size = {team_size}, Industry = {industry}

Return:
{{
  "process_name": "...",
  "summary": "One sentence describing what this process achieves",
  "steps": [
    {{"id": 1, "name": "...", "description": "...", "owner": "role responsible", "duration_estimate": "e.g. 1 day", "tools": ["tool1", "tool2"]}}
  ],
  "automations": [
    {{"step_ref": 1, "what": "What can be automated", "how": "Specific tool or method", "time_saved": "e.g. 2h/week", "complexity": "Low|Medium|High"}}
  ],
  "decision_points": [
    {{"after_step": 1, "question": "Key decision to make", "if_yes": "Next action", "if_no": "Alternative path", "criteria": "How to decide"}}
  ],
  "systems_score": {{
    "scalability": 1-10,
    "automation_potential": 1-10,
    "clarity": 1-10,
    "overall_readiness": 1-10
  }}
}}

Return ONLY the JSON. No text before or after."""

        with st.spinner("Mapping your process..."):
            raw = call_claude(PROMPT, SYSTEM)

        if raw:
            data = parse_json_block(raw)
            if not data:
                st.error("Could not parse response. Raw output:")
                st.code(raw)
            else:
                st.markdown(f"## {data.get('process_name', process_input)}")
                st.info(data.get("summary", ""))

                # Score cards
                score = data.get("systems_score", {})
                s1, s2, s3, s4 = st.columns(4)
                for col, label, key, color in [
                    (s1, "Scalability", "scalability", "#38bdf8"),
                    (s2, "Automation Potential", "automation_potential", "#34d399"),
                    (s3, "Clarity", "clarity", "#f59e0b"),
                    (s4, "Overall Readiness", "overall_readiness", "#a78bfa"),
                ]:
                    with col:
                        val = score.get(key, "—")
                        st.markdown(f"""<div class="card">
                            <div class="score-ring" style="color:{color}">{val}/10</div>
                            <div class="score-label">{label}</div>
                        </div>""", unsafe_allow_html=True)

                c_steps, c_auto, c_dec = st.columns(3)

                with c_steps:
                    st.markdown("### 📋 Steps")
                    for s in data.get("steps", []):
                        st.markdown(f"""<div class="card card-step">
                            <span class="badge badge-step">Step {s['id']}</span>
                            <strong style="color:#e2e8f0">{s['name']}</strong><br>
                            <span style="color:#94a3b8;font-size:0.85rem">{s['description']}</span><br><br>
                            <span style="color:#64748b;font-size:0.8rem">👤 {s.get('owner','')} &nbsp;·&nbsp; ⏱ {s.get('duration_estimate','')} &nbsp;·&nbsp; 🛠 {', '.join(s.get('tools',[]))}</span>
                        </div>""", unsafe_allow_html=True)

                with c_auto:
                    st.markdown("### 🤖 Automations")
                    for a in data.get("automations", []):
                        complexity_color = {"Low": "#34d399", "Medium": "#f59e0b", "High": "#f87171"}.get(a.get("complexity", ""), "#94a3b8")
                        st.markdown(f"""<div class="card card-auto">
                            <span class="badge badge-auto">Step {a.get('step_ref','?')} → Automate</span>
                            <strong style="color:#e2e8f0">{a['what']}</strong><br>
                            <span style="color:#94a3b8;font-size:0.85rem">{a['how']}</span><br><br>
                            <span style="color:#34d399;font-size:0.8rem">⚡ {a.get('time_saved','')} saved</span>
                            &nbsp;&nbsp;<span style="color:{complexity_color};font-size:0.8rem">Complexity: {a.get('complexity','')}</span>
                        </div>""", unsafe_allow_html=True)

                with c_dec:
                    st.markdown("### ⚡ Decision Points")
                    for d in data.get("decision_points", []):
                        st.markdown(f"""<div class="card card-decision">
                            <span class="badge badge-decision">After Step {d.get('after_step','?')}</span>
                            <strong style="color:#e2e8f0">{d['question']}</strong><br><br>
                            <span style="color:#34d399;font-size:0.8rem">✅ Yes → {d['if_yes']}</span><br>
                            <span style="color:#f87171;font-size:0.8rem">❌ No → {d['if_no']}</span><br><br>
                            <span style="color:#64748b;font-size:0.8rem">📐 {d.get('criteria','')}</span>
                        </div>""", unsafe_allow_html=True)

    elif analyze_btn:
        st.warning("Please describe a process first.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Client Operations Optimizer
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Client Operations Optimizer")
    st.caption("Simulate a client lifecycle, surface bottlenecks, and get a quantified efficiency score.")

    col_a, col_b = st.columns(2)
    with col_a:
        client_type = st.text_input("Client type / segment", placeholder="e.g. Mid-market SaaS company, 50 employees")
        workflow_desc = st.text_area(
            "Current workflow / process description",
            placeholder="e.g. Sales hands off to CS via email. CS schedules kickoff manually. Onboarding docs sent as PDFs. Weekly check-ins tracked in a spreadsheet. No automated health scoring.",
            height=130,
        )
    with col_b:
        pain_points = st.text_area(
            "Known pain points (optional)",
            placeholder="e.g. Clients go dark after week 2, renewals often surprise us, manual reporting takes 3h/week",
            height=80,
        )
        team_capacity = st.text_input("Team capacity / constraints", placeholder="e.g. 1 CS manager, no dedicated ops")

    optimize_btn = st.button("Optimize Operations →", type="primary", use_container_width=True)

    if optimize_btn and workflow_desc.strip():
        SYSTEM2 = """You are a world-class operations consultant specializing in client success and revenue operations.
You identify inefficiencies with surgical precision, quantify their cost, and design scalable fixes.
Always respond with valid JSON only."""

        PROMPT2 = f"""Analyze this client operations setup and return a JSON object.

Client segment: {client_type or 'Not specified'}
Current workflow: {workflow_desc}
Known pain points: {pain_points or 'Not specified'}
Team capacity: {team_capacity or 'Not specified'}

Return:
{{
  "lifecycle_stages": [
    {{"stage": "e.g. Onboarding", "current_state": "...", "health": "Poor|Fair|Good"}}
  ],
  "bottlenecks": [
    {{"id": 1, "stage": "...", "issue": "What is broken", "root_cause": "Why it happens", "impact": "Business impact", "severity": "Critical|High|Medium|Low"}}
  ],
  "automation_suggestions": [
    {{"bottleneck_ref": 1, "action": "What to automate or systematize", "tool_suggestion": "Specific tool or approach", "effort": "Low|Medium|High", "roi": "Expected outcome"}}
  ],
  "quick_wins": [
    "Short actionable string you can do this week"
  ],
  "efficiency_score": {{
    "current": 1-100,
    "potential": 1-100,
    "score_breakdown": {{
      "process_clarity": 1-10,
      "automation_level": 1-10,
      "client_visibility": 1-10,
      "team_leverage": 1-10
    }},
    "headline": "One sentence summary of the current state"
  }}
}}

Return ONLY the JSON."""

        with st.spinner("Analyzing client operations..."):
            raw2 = call_claude(PROMPT2, SYSTEM2)

        if raw2:
            data2 = parse_json_block(raw2)
            if not data2:
                st.error("Could not parse response. Raw output:")
                st.code(raw2)
            else:
                eff = data2.get("efficiency_score", {})
                current = eff.get("current", 0)
                potential = eff.get("potential", 0)

                # Efficiency Score header
                m1, m2, m3 = st.columns([1, 2, 1])
                with m2:
                    score_color = "#f87171" if current < 40 else "#f59e0b" if current < 70 else "#34d399"
                    st.markdown(f"""<div class="card" style="text-align:center">
                        <div style="font-size:0.85rem;color:#94a3b8;margin-bottom:0.3rem">CURRENT EFFICIENCY SCORE</div>
                        <div style="font-size:4rem;font-weight:800;color:{score_color}">{current}<span style="font-size:1.5rem;color:#64748b">/100</span></div>
                        <div style="color:#34d399;font-size:0.9rem;margin-top:0.2rem">→ Potential: {potential}/100 (+{potential - current} pts with fixes)</div>
                        <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.5rem;font-style:italic">{eff.get('headline','')}</div>
                    </div>""", unsafe_allow_html=True)

                # Sub-scores
                breakdown = eff.get("score_breakdown", {})
                b1, b2, b3, b4 = st.columns(4)
                for col, label, key, color in [
                    (b1, "Process Clarity", "process_clarity", "#38bdf8"),
                    (b2, "Automation Level", "automation_level", "#34d399"),
                    (b3, "Client Visibility", "client_visibility", "#f59e0b"),
                    (b4, "Team Leverage", "team_leverage", "#a78bfa"),
                ]:
                    with col:
                        val = breakdown.get(key, "—")
                        st.markdown(f"""<div class="card" style="text-align:center">
                            <div style="font-size:1.8rem;font-weight:700;color:{color}">{val}/10</div>
                            <div style="color:#94a3b8;font-size:0.8rem">{label}</div>
                        </div>""", unsafe_allow_html=True)

                # Lifecycle stages
                st.markdown("### 🔄 Client Lifecycle Map")
                stages = data2.get("lifecycle_stages", [])
                stage_cols = st.columns(len(stages)) if stages else []
                health_colors = {"Poor": "#f87171", "Fair": "#f59e0b", "Good": "#34d399"}
                for i, stage in enumerate(stages):
                    with stage_cols[i]:
                        h = stage.get("health", "Fair")
                        c = health_colors.get(h, "#94a3b8")
                        st.markdown(f"""<div class="card" style="text-align:center;border-left:4px solid {c}">
                            <div style="font-weight:700;color:#e2e8f0">{stage['stage']}</div>
                            <div style="color:{c};font-size:0.8rem;font-weight:600">{h}</div>
                            <div style="color:#94a3b8;font-size:0.8rem;margin-top:0.4rem">{stage.get('current_state','')}</div>
                        </div>""", unsafe_allow_html=True)

                # Bottlenecks + Automations
                left, right = st.columns(2)

                with left:
                    st.markdown("### 🚧 Bottlenecks")
                    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                    bottlenecks = sorted(data2.get("bottlenecks", []), key=lambda x: severity_order.get(x.get("severity", "Low"), 3))
                    for b in bottlenecks:
                        sev = b.get("severity", "Medium")
                        sev_color = {"Critical": "#f87171", "High": "#fb923c", "Medium": "#f59e0b", "Low": "#94a3b8"}.get(sev, "#94a3b8")
                        st.markdown(f"""<div class="card card-bottleneck">
                            <span class="badge badge-bottleneck">{b.get('stage','')} · {sev}</span>
                            <strong style="color:#e2e8f0">{b['issue']}</strong><br>
                            <span style="color:#94a3b8;font-size:0.85rem">Root cause: {b.get('root_cause','')}</span><br>
                            <span style="color:{sev_color};font-size:0.8rem">Impact: {b.get('impact','')}</span>
                        </div>""", unsafe_allow_html=True)

                with right:
                    st.markdown("### ✅ Automation Suggestions")
                    for a in data2.get("automation_suggestions", []):
                        effort_color = {"Low": "#34d399", "Medium": "#f59e0b", "High": "#f87171"}.get(a.get("effort", ""), "#94a3b8")
                        st.markdown(f"""<div class="card card-suggestion">
                            <span class="badge badge-suggestion">Fix #{a.get('bottleneck_ref','?')}</span>
                            <strong style="color:#e2e8f0">{a['action']}</strong><br>
                            <span style="color:#94a3b8;font-size:0.85rem">🛠 {a.get('tool_suggestion','')}</span><br><br>
                            <span style="color:{effort_color};font-size:0.8rem">Effort: {a.get('effort','')}</span>
                            &nbsp;&nbsp;<span style="color:#38bdf8;font-size:0.8rem">ROI: {a.get('roi','')}</span>
                        </div>""", unsafe_allow_html=True)

                # Quick wins
                st.markdown("### ⚡ Quick Wins — Do This Week")
                qw = data2.get("quick_wins", [])
                for i, win in enumerate(qw, 1):
                    st.markdown(f"""<div class="card" style="border-left:4px solid #34d399;padding:0.8rem 1.2rem">
                        <span style="color:#34d399;font-weight:700">{i}.</span>
                        <span style="color:#e2e8f0"> {win}</span>
                    </div>""", unsafe_allow_html=True)

    elif optimize_btn:
        st.warning("Please describe the current workflow first.")
