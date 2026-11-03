import html
import json
from pathlib import Path

import streamlit as st

from src.config import ensure_api_key, STUDENTS_DB_FILE
from src.agent import StudentSupportAgent
from src.policy_retriever import PolicyRetriever
from src.memory import MemoryManager
from src.approvals import (
    request_fee_waiver,
    list_pending_approvals,
    decide_approval,
)


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="CampusAI | Student Support",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------
# Visual design
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --page: #f4f6fb;
        --surface: #ffffff;
        --surface-soft: #f8faff;
        --ink: #17223b;
        --muted: #68758f;
        --line: #e4e9f2;
        --navy: #111b34;
        --blue: #4263eb;
        --blue-soft: #edf2ff;
        --violet: #7557d9;
        --green: #16865d;
        --shadow: 0 10px 30px rgba(20, 35, 70, 0.06);
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: var(--page);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(244, 246, 251, 0.88);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 1.4rem;
        padding-bottom: 3.5rem;
    }

    h1, h2, h3, h4 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--ink);
        letter-spacing: -0.45px;
    }

    p, li, label {
        color: var(--ink);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #111a2e;
        border-right: 1px solid #26334e;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #e8eefb !important;
    }

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #99a8c2 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #ffffff;
        border: 1px solid #dbe3f0;
        border-radius: 10px;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #17223b;
    }

    .sidebar-brand {
        font-family: 'Manrope', sans-serif;
        font-size: 1.28rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.8px;
        padding: 0.3rem 0 0.1rem 0;
    }

    .sidebar-brand span {
        color: #91a9ff;
    }

    .sidebar-kicker {
        color: #93a3bf;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 1.8px;
        margin-bottom: 1.15rem;
    }

    .sidebar-profile {
        background: linear-gradient(145deg, #1b2945, #172239);
        border: 1px solid #334362;
        border-radius: 15px;
        padding: 15px;
        margin: 0.5rem 0 1.1rem 0;
    }

    .sidebar-profile-label {
        color: #9eafd0;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 1.25px;
        margin-bottom: 5px;
    }

    .sidebar-profile-name {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .sidebar-profile-value {
        color: #e3eaff;
        font-size: 0.84rem;
        font-weight: 600;
        overflow-wrap: anywhere;
    }

    .sidebar-note {
        color: #96a5bd;
        font-size: 0.72rem;
        line-height: 1.55;
        padding-top: 0.5rem;
    }

    /* Sidebar action buttons: enforce readable contrast on dark navigation */
    [data-testid="stSidebar"] .stButton > button {
        background: #f7f9ff !important;
        color: #1b2b49 !important;
        border: 1px solid #d5def0 !important;
        border-radius: 11px !important;
        min-height: 2.65rem;
        height: auto;
        padding: 0.62rem 0.72rem;
        white-space: normal;
        line-height: 1.3;
        box-shadow: 0 2px 7px rgba(0, 0, 0, 0.10);
    }

    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span,
    [data-testid="stSidebar"] .stButton > button div {
        color: #1b2b49 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #e9efff !important;
        border-color: #aebff4 !important;
        color: #173b9a !important;
    }

    [data-testid="stSidebar"] .stButton > button:focus {
        outline: 2px solid #91a9ff !important;
        outline-offset: 2px;
    }

    /* Improve contrast of small supporting labels in the main workspace */
    .topline-brand {
        color: #263653 !important;
        opacity: 1 !important;
    }

    .topline-note {
        color: #65738e !important;
        opacity: 1 !important;
    }

    .section-kicker {
        color: #536582 !important;
    }

    .section-copy {
        color: #596985 !important;
    }

    .student-highlight-kicker,
    .student-highlight-id,
    .profile-field-label {
        color: #5c6b85 !important;
    }

    /* Main heading and hero */
    .topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .topline-brand {
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 0.95rem;
        color: #263653;
        letter-spacing: -0.35px;
    }

    .topline-note {
        color: #73809a;
        font-size: 0.78rem;
    }

    .hero-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(118deg, #17294b 0%, #294b91 58%, #5d62c7 100%);
        border-radius: 23px;
        padding: 2rem 2.15rem;
        color: #ffffff;
        box-shadow: 0 16px 38px rgba(38, 65, 132, 0.16);
        min-height: 230px;
    }

    .hero-card:after {
        content: '';
        position: absolute;
        width: 280px;
        height: 280px;
        right: -70px;
        top: -115px;
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 50%;
        box-shadow: 0 0 0 32px rgba(255,255,255,0.035), 0 0 0 67px rgba(255,255,255,0.025);
        pointer-events: none;
    }

    .hero-eyebrow {
        color: #c9d7ff;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.65rem;
    }

    .hero-title {
        color: #ffffff;
        font-family: 'Manrope', sans-serif;
        font-size: clamp(1.8rem, 3.5vw, 2.75rem);
        line-height: 1.12;
        letter-spacing: -1.1px;
        font-weight: 800;
        margin: 0 0 0.75rem 0;
        max-width: 700px;
    }

    .hero-copy {
        color: #dbe5ff;
        max-width: 690px;
        font-size: 0.94rem;
        line-height: 1.65;
        margin-bottom: 1.1rem;
    }

    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #edf2ff;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
    }

    .student-highlight {
        height: 100%;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.35rem;
        box-shadow: var(--shadow);
    }

    .student-highlight-kicker {
        color: #77839b;
        font-size: 0.67rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
    }

    .student-avatar {
        width: 43px;
        height: 43px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #edf2ff;
        color: #4263eb;
        font-family: 'Manrope', sans-serif;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.75rem;
    }

    .student-highlight-name {
        font-family: 'Manrope', sans-serif;
        color: #192641;
        font-size: 1.08rem;
        font-weight: 800;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }

    .student-highlight-id {
        color: #697791;
        font-size: 0.8rem;
        margin: 0.25rem 0 0.9rem 0;
    }

    .student-highlight-programme {
        color: #394967;
        font-size: 0.83rem;
        line-height: 1.5;
        font-weight: 600;
        padding-top: 0.8rem;
        border-top: 1px solid #edf0f6;
    }

    /* Cards, tabs, metrics */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 15px;
        padding: 14px 16px;
        box-shadow: 0 5px 18px rgba(20, 35, 70, 0.035);
    }

    div[data-testid="stMetric"] label {
        color: #72809a !important;
        font-size: 0.77rem !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1c2b49 !important;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
    }

    .section-kicker {
        color: #71809b;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.67rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .section-title {
        color: #192641;
        font-family: 'Manrope', sans-serif;
        font-size: 1.28rem;
        font-weight: 800;
        letter-spacing: -0.45px;
        margin-bottom: 0.2rem;
    }

    .section-copy {
        color: #71809a;
        font-size: 0.86rem;
        line-height: 1.55;
        margin-bottom: 0.8rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e3e8f1;
    }

    [data-testid="stTabs"] button[role="tab"] {
        background: transparent;
        color: #64728c;
        border-radius: 10px 10px 0 0;
        padding: 0.7rem 1rem;
        font-weight: 700;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #3659dc;
        border-bottom: 3px solid #4263eb;
    }

    /* Chat */
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e5eaf3;
        border-radius: 17px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 14px rgba(20, 35, 70, 0.035);
    }

    [data-testid="stChatInput"] {
        background: #ffffff;
        border: 1px solid #dce4f1;
        border-radius: 17px;
        box-shadow: 0 8px 24px rgba(25, 45, 85, 0.07);
    }

    [data-testid="stChatInput"] textarea {
        color: #1c2b49 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #8a96aa !important;
    }

    /* Buttons and form controls */
    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 11px;
        min-height: 2.55rem;
        font-weight: 700;
        border: 1px solid #dce4f1;
        transition: all 0.15s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #9eb2f8;
        color: #3659dc;
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(105deg, #4263eb, #6958d9);
        color: #ffffff;
        border: 0;
    }

    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #e3e9f2;
        border-radius: 13px;
    }

    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #e5eaf3;
        border-radius: 15px;
        padding: 1rem;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    .soft-note {
        background: #f0f4ff;
        border: 1px solid #dce5ff;
        color: #53658d;
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
        font-size: 0.78rem;
        line-height: 1.5;
    }

    .profile-field {
        background: #ffffff;
        border: 1px solid #e5eaf3;
        border-radius: 13px;
        padding: 0.85rem 1rem;
        min-height: 82px;
        margin-bottom: 0.25rem;
    }

    .profile-field-label {
        color: #79869d;
        text-transform: uppercase;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 0.35rem;
    }

    .profile-field-value {
        color: #1d2b48;
        font-size: 0.92rem;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    hr {
        border-color: #e5eaf3;
    }

    @media (max-width: 800px) {
        .block-container { padding-top: 0.8rem; }
        .hero-card { padding: 1.45rem; }
        .hero-title { font-size: 1.9rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Data and agent initialization
# ---------------------------------------------------------
@st.cache_data
def load_students():
    """Load the demonstration student records from the project data folder."""
    if not STUDENTS_DB_FILE.exists():
        return {}

    with open(STUDENTS_DB_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_agent():
    """Create one agent instance per Streamlit user session."""
    if "agent_instance" not in st.session_state:
        st.session_state.agent_instance = StudentSupportAgent(
            retriever=PolicyRetriever(),
            memory=MemoryManager(),
        )
    return st.session_state.agent_instance


def display_value(value):
    """Convert a record value into readable text for the profile page."""
    if value is None or value == "":
        return "Not provided"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) or "Not provided"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def render_agent_details(meta):
    """Show transparent details about tools, retrieval, memory and usage."""
    with st.expander("Agent activity · tools, evidence and performance"):
        tools_used = meta.get("tools_used") or []
        evidence = meta.get("retrieved_evidence") or []

        left, right = st.columns(2)
        with left:
            st.markdown("**Tools used**")
            if tools_used:
                for tool_name in tools_used:
                    st.write(f"• `{tool_name}`")
            else:
                st.caption("No tool calls were needed for this response.")

        with right:
            st.markdown("**Performance**")
            st.write(f"Latency: {meta.get('latency_seconds', 0)} seconds")
            st.write(f"Total tokens: {meta.get('total_tokens', 0)}")

        if evidence:
            st.markdown("**Retrieved evidence**")
            for item in evidence:
                st.write(f"• {item}")

        if meta.get("memory_notice"):
            st.info(meta["memory_notice"])


# ---------------------------------------------------------
# Initialize data, API key and agent
# ---------------------------------------------------------
try:
    students = load_students()

    if not students:
        st.error("No student records found. Check data/students_db.json.")
        st.stop()

    # Uses the same local Groq key configured for main.py.
    ensure_api_key(interactive=False)
    agent = get_agent()
except Exception as exc:
    st.error(
        "The application could not initialize. Check your .env configuration "
        "and installed dependencies."
    )
    st.code(f"{type(exc).__name__}: {exc}")
    st.stop()


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "active_student_id" not in st.session_state:
    st.session_state.active_student_id = (
        "STU101" if "STU101" in students else next(iter(students))
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_history" not in st.session_state:
    st.session_state.agent_history = []


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">✦ Campus<span>AI</span></div>'
        '<div class="sidebar-kicker">INTELLIGENT STUDENT SUPPORT</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("#### Student workspace")
    st.caption("Choose a demo student profile. This is not authentication.")

    student_ids = list(students.keys())
    current_index = (
        student_ids.index(st.session_state.active_student_id)
        if st.session_state.active_student_id in student_ids
        else 0
    )

    selected_student = st.selectbox(
        "Active student",
        student_ids,
        index=current_index,
        format_func=lambda sid: (
            f"{students[sid].get('full_name', sid)} · {sid}"
        ),
        label_visibility="collapsed",
    )

    if selected_student != st.session_state.active_student_id:
        st.session_state.active_student_id = selected_student
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.rerun()

    student = students[selected_student]
    student_name = str(student.get("full_name", selected_student))
    student_programme = str(student.get("programme", "Not specified"))
    initials = "".join(part[0] for part in student_name.split()[:2] if part).upper()
    initials = initials or "ST"

    st.markdown(
        f"""
        <div class="sidebar-profile">
            <div class="sidebar-profile-label">ACTIVE PROFILE</div>
            <div class="sidebar-profile-name">{html.escape(student_name)}</div>
            <div class="sidebar-profile-label" style="margin-top:13px">STUDENT ID</div>
            <div class="sidebar-profile-value">{html.escape(selected_student)}</div>
            <div class="sidebar-profile-label" style="margin-top:11px">PROGRAMME</div>
            <div class="sidebar-profile-value">{html.escape(student_programme)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Quick actions")
    quick_prompts = [
        "What is my current fee status?",
        "Check my academic profile.",
        "What is the scholarship eligibility policy?",
        "The payment portal is failing. What should I do?",
    ]

    for i, prompt in enumerate(quick_prompts):
        if st.button(prompt, key=f"quick_{i}", use_container_width=True):
            st.session_state.pending_prompt = prompt
            st.rerun()

    st.divider()
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.rerun()

    st.markdown(
        """
        <div class="sidebar-note">
            Prototype environment. Responses are AI-generated and should be
            checked against official institute policies. Student selection is
            for demonstration only and does not authenticate a user.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Main header and student summary
# ---------------------------------------------------------
st.markdown(
    """
    <div class="topline">
        <div class="topline-brand">CAMPUSAI <span style="color:#4263eb">/</span> STUDENT SERVICES</div>
        <div class="topline-note">Your digital campus assistant</div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_col, student_col = st.columns([1.85, 0.95], gap="large")

with hero_col:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-eyebrow">YOUR DIGITAL CAMPUS ASSISTANT</div>
            <div class="hero-title">A smarter way to get<br>student support.</div>
            <div class="hero-copy">
                Ask about fees, academic records, scholarships, institute
                policies or student support. The assistant can retrieve relevant
                handbook information and use available student-service tools.
            </div>
            <span class="hero-chip">● AI assistant ready</span>
            <span class="hero-chip">✦ Policy-grounded support</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with student_col:
    st.markdown(
        f"""
        <div class="student-highlight">
            <div class="student-highlight-kicker">CURRENT STUDENT</div>
            <div class="student-avatar">{html.escape(initials)}</div>
            <div class="student-highlight-name">{html.escape(student_name)}</div>
            <div class="student-highlight-id">Student ID · {html.escape(selected_student)}</div>
            <div class="student-highlight-programme">{html.escape(student_programme)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.metric("Conversation messages", len(st.session_state.messages))
with metric2:
    st.metric("Active student", selected_student)
with metric3:
    st.metric("Assistant status", "Ready")

st.write("")
assistant_tab, profile_tab, approvals_tab = st.tabs(
    ["✦  AI Assistant", "▦  Student profile", "✓  Human approvals"]
)


# ---------------------------------------------------------
# AI assistant tab
# ---------------------------------------------------------
with assistant_tab:
    st.markdown(
        '<div class="section-kicker">CONVERSATION</div>'
        '<div class="section-title">How can we help?</div>'
        '<div class="section-copy">Ask a question or choose a quick action from the sidebar.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        st.info(
            "Welcome! I can help with fee status, academic records, scholarship "
            "policies, handbook questions and support requests."
        )

    # Render earlier conversation messages.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("meta"):
                render_agent_details(message["meta"])

    # Chat input also accepts a prompt selected from the sidebar.
    pending_prompt = st.session_state.pop("pending_prompt", None)
    user_prompt = st.chat_input("Type your student support question here…")

    if pending_prompt or user_prompt:
        question = pending_prompt or user_prompt

        st.session_state.messages.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Reviewing your question and relevant information…"):
                try:
                    output = agent.process_query(
                        query=question,
                        student_id=st.session_state.active_student_id,
                        session_history=st.session_state.agent_history,
                    )

                    answer = output.get(
                        "answer",
                        "Sorry, I couldn't produce a response.",
                    )
                    if not answer:
                        answer = "Sorry, I couldn't produce a response."

                    meta = {
                        "tools_used": output.get("tools_used", []),
                        "retrieved_evidence": output.get("retrieved_evidence", []),
                        "memory_notice": output.get("memory_notice", ""),
                        "latency_seconds": output.get("latency_seconds", 0),
                        "total_tokens": output.get("total_tokens", 0),
                    }

                    st.markdown(answer)
                    render_agent_details(meta)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "meta": meta,
                    })

                    # Keep the same history format used by the terminal agent.
                    st.session_state.agent_history.extend([
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer},
                    ])

                except Exception as exc:
                    st.error(
                        "Something went wrong while processing this request. "
                        "Check the VS Code terminal for the technical error. "
                        "Do not share passwords, OTPs or API keys."
                    )
                    st.caption(f"Technical detail: {type(exc).__name__}")

    st.markdown(
        '<div class="soft-note">Privacy reminder: do not enter passwords, OTPs, '
        'or other confidential login credentials into the demo assistant.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Student profile tab
# ---------------------------------------------------------
with profile_tab:
    st.markdown(
        '<div class="section-kicker">STUDENT RECORD</div>'
        '<div class="section-title">Student profile</div>'
        '<div class="section-copy">Profile information available in the local demonstration database.</div>',
        unsafe_allow_html=True,
    )

    profile_fields = [
        ("Student name", "full_name"),
        ("Student ID", None),
        ("Programme", "programme"),
        ("Department", "department"),
        ("Semester", "semester"),
        ("Year", "year"),
        ("CGPA", "cgpa"),
        ("Academic advisor", "advisor"),
        ("Academic interests", "academic_interests"),
    ]

    available_fields = []
    for label, key in profile_fields:
        if key is None:
            value = selected_student
            available_fields.append((label, value))
        elif key in student and student.get(key) not in (None, ""):
            available_fields.append((label, display_value(student.get(key))))

    if available_fields:
        for start in range(0, len(available_fields), 3):
            row_fields = available_fields[start:start + 3]
            cols = st.columns(3)
            for col, (label, value) in zip(cols, row_fields):
                with col:
                    st.markdown(
                        f"""
                        <div class="profile-field">
                            <div class="profile-field-label">{html.escape(label)}</div>
                            <div class="profile-field-value">{html.escape(str(value))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No additional profile fields are available for this student.")

    st.markdown(
        '<div class="soft-note">This page displays only fields present in '
        'data/students_db.json. It does not create or estimate missing academic data.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Human approvals tab
# ---------------------------------------------------------
with approvals_tab:
    st.markdown(
        '<div class="section-kicker">HUMAN-IN-THE-LOOP</div>'
        '<div class="section-title">Fee-waiver approvals</div>'
        '<div class="section-copy">Submit a fee-waiver request or review requests waiting for a decision.</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "Demonstration workflow only: the selected student identity is not an "
        "authenticated reviewer account. Do not use this prototype for real approvals."
    )

    request_col, queue_col = st.columns([1, 1.25], gap="large")

    with request_col:
        st.markdown("#### Request a fee waiver")
        with st.form("waiver_request_form"):
            waiver_amount = st.number_input(
                "Requested waiver amount (₹)",
                min_value=1,
                max_value=1000000,
                value=10000,
                step=1000,
            )
            waiver_reason = st.text_area(
                "Reason for request",
                placeholder="Explain why this fee adjustment is being requested.",
                max_chars=500,
            )
            submit_waiver = st.form_submit_button(
                "Submit for approval",
                type="primary",
                use_container_width=True,
            )

        if submit_waiver:
            if not waiver_reason.strip():
                st.warning("Please provide a reason for the request.")
            else:
                try:
                    result = request_fee_waiver(
                        student_id=st.session_state.active_student_id,
                        amount=int(waiver_amount),
                        reason=waiver_reason.strip(),
                    )
                    if result.get("status") == "success":
                        st.success(result["message"])
                    else:
                        st.error(result.get("message", "Request failed."))
                except Exception as exc:
                    st.error(f"Could not submit the request: {type(exc).__name__}")

    with queue_col:
        st.markdown("#### Pending requests")
        try:
            pending_requests = list_pending_approvals()
        except Exception as exc:
            pending_requests = []
            st.error(f"Could not load pending requests: {type(exc).__name__}")

        if not pending_requests:
            st.info("There are no pending requests.")
        else:
            for request in pending_requests:
                request_id = request["request_id"]
                with st.container(border=True):
                    st.markdown(f"**{request_id}** · {request['requester_id']}")
                    st.write(f"Requested amount: ₹{request['amount']:,}")
                    st.write(f"Reason: {request['reason']}")
                    st.write(
                        f"Balance when requested: ₹{request['balance_before']:,}"
                    )

                    approve_col, reject_col = st.columns(2)
                    with approve_col:
                        if st.button(
                            "Approve",
                            key=f"approve_{request_id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                result = decide_approval(
                                    request_id=request_id,
                                    decision="APPROVE",
                                    approver_id=st.session_state.active_student_id,
                                )
                                if result.get("status") == "success":
                                    st.success(result["message"])
                                else:
                                    st.error(result.get("message", "Approval failed."))
                            except Exception as exc:
                                st.error(f"Approval failed: {type(exc).__name__}")
                            st.rerun()

                    with reject_col:
                        if st.button(
                            "Reject",
                            key=f"reject_{request_id}",
                            use_container_width=True,
                        ):
                            try:
                                result = decide_approval(
                                    request_id=request_id,
                                    decision="REJECT",
                                    approver_id=st.session_state.active_student_id,
                                )
                                if result.get("status") == "success":
                                    st.warning(result["message"])
                                else:
                                    st.error(result.get("message", "Rejection failed."))
                            except Exception as exc:
                                st.error(f"Rejection failed: {type(exc).__name__}")
                            st.rerun()

st.write("")
st.caption(
    "CampusAI Student Support · Academic, fee and policy assistance · "
    "Prototype interface"
)
