"""
app.py – Streamlit UI for the Multi-Agent Debate System
"""

import os
import streamlit as st
from dotenv import load_dotenv
from agents import DebaterAgent, JudgeAgent, run_debate, DEBATE_MODEL, JUDGE_MODEL

load_dotenv()

DEFAULT_ROUNDS = int(os.getenv("DEBATE_ROUNDS", "2"))

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚔️ Multi-Agent Debate Arena",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .for-box {
        background: linear-gradient(135deg, #1a3a1a, #0f2d0f);
        border: 1px solid #2d6a2d;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .against-box {
        background: linear-gradient(135deg, #3a1a1a, #2d0f0f);
        border: 1px solid #6a2d2d;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .judge-box {
        background: linear-gradient(135deg, #1a1a3a, #0f0f2d);
        border: 2px solid #4a4a8a;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
    }
    .round-header {
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 8px;
        color: #aaaaaa;
    }
    .winner-badge {
        font-size: 2em;
        text-align: center;
        padding: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-size: 1.1em;
        font-weight: bold;
    }
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Debate Settings")
    st.divider()

    debate_model = st.text_input(
        "🤖 Debater Model",
        value=DEBATE_MODEL,
        help="Ollama model used for both FOR and AGAINST agents"
    )
    judge_model = st.text_input(
        "👨‍⚖️ Judge Model",
        value=JUDGE_MODEL,
        help="Ollama model used for the judge agent"
    )
    rounds = st.slider(
        "🔄 Debate Rounds",
        min_value=1,
        max_value=4,
        value=DEFAULT_ROUNDS,
        help="More rounds = deeper rebuttals but longer runtime"
    )

    st.divider()
    st.markdown("### 💡 Example Questions")
    example_questions = [
        "Should AI be given legal personhood?",
        "Is remote work better than office work?",
        "Should social media platforms be regulated like utilities?",
        "Is nuclear energy the solution to climate change?",
        "Should humans colonize Mars?",
        "Is universal basic income economically viable?",
    ]
    for q in example_questions:
        if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
            st.session_state["question_input"] = q
            st.rerun()

    st.divider()
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    ```
    Question
       │
       ├─► Agent FOR  ────┐
       │   (llm + memory) │
       │                  ├─► Judge Agent
       ├─► Agent AGAINST ─┘   (verdict)
           (llm + memory)
    ```
    """)
    st.markdown("**Each agent keeps full conversation history across rounds.**")


# ── Main UI ────────────────────────────────────────────────────────────────────
st.title("⚔️ Multi-Agent Debate Arena")
st.caption(
    "Two AI agents argue opposite sides of any question. "
    "A third judge agent evaluates and picks the stronger argument."
)

# Warn about LLM limitations – this is a hackathon talking point!
with st.expander("🧠 Why Multi-Agent Debate? (Hackathon Context)", expanded=False):
    st.markdown("""
    **LLM Limitations this project addresses:**

    | Problem | How Debate Helps |
    |---------|-----------------|
    | 🎭 **Sycophancy** | Agents are *forced* to argue a position, not just agree with the user |
    | 🌫️ **Hallucination** | Opponent agents fact-check and rebut weak claims |
    | 🎯 **Bias** | Seeing both sides exposes assumptions hidden in a single-model answer |
    | 📉 **Overconfidence** | Judge scoring creates calibrated confidence signals |

    **Architecture:** 3 agents × same base model = diversity through *role forcing*, not model diversity.
    """)

st.divider()

# Question Input
if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

question = st.text_input(
    "🎯 Enter your debate question:",
    value=st.session_state["question_input"],
    placeholder="e.g. Should AI be given legal personhood?",
    key="question_input_widget",
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    start_btn = st.button("🚀 Start Debate", type="primary", use_container_width=True)

# ── Debate Execution ───────────────────────────────────────────────────────────
if start_btn:
    if not question.strip():
        st.error("⚠️ Please enter a debate question first.")
        st.stop()

    # Clear previous results
    st.session_state.pop("debate_result", None)

    st.divider()
    st.markdown(f"### 🎯 Topic: *{question}*")
    st.markdown(f"**Model:** `{debate_model}` | **Rounds:** `{rounds}` | **Judge:** `{judge_model}`")

    # ── Streaming debate with live updates ──────────────────────────────────
    for_agent     = DebaterAgent("FOR",     model=debate_model)
    against_agent = DebaterAgent("AGAINST", model=debate_model)
    judge_agent   = JudgeAgent(model=judge_model)

    for_args:     list[str] = []
    against_args: list[str] = []

    for r in range(1, rounds + 1):
        st.markdown(f"---")
        st.markdown(f"### 🔄 Round {r}")

        col_for, col_against = st.columns(2)

        # FOR agent
        with col_for:
            with st.spinner(f"🟢 FOR agent arguing (Round {r})..."):
                against_last = against_args[-1] if against_args else ""
                f_arg = for_agent.argue(question, against_last, round_num=r)
                for_args.append(f_arg)

            st.markdown(
                f'<div class="for-box">'
                f'<div class="round-header">🟢 FOR (Round {r})</div>'
                f'{f_arg}</div>',
                unsafe_allow_html=True,
            )

        # AGAINST agent
        with col_against:
            with st.spinner(f"🔴 AGAINST agent arguing (Round {r})..."):
                for_last = for_args[-1] if for_args else ""
                a_arg = against_agent.argue(question, for_last, round_num=r)
                against_args.append(a_arg)

            st.markdown(
                f'<div class="against-box">'
                f'<div class="round-header">🔴 AGAINST (Round {r})</div>'
                f'{a_arg}</div>',
                unsafe_allow_html=True,
            )

    # ── Judge ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 👨‍⚖️ Judge Deliberating...")

    with st.spinner("Judge is evaluating both sides..."):
        verdict = judge_agent.judge(question, for_args, against_args)

    # Determine winner for badge
    winner_badge = "🏆"
    if "**WINNER**: FOR" in verdict or "WINNER: FOR" in verdict:
        winner_badge = "🟢 FOR wins!"
    elif "**WINNER**: AGAINST" in verdict or "WINNER: AGAINST" in verdict:
        winner_badge = "🔴 AGAINST wins!"
    elif "TIE" in verdict:
        winner_badge = "🤝 It's a TIE!"

    st.markdown(
        f'<div class="judge-box">'
        f'<div class="winner-badge">{winner_badge}</div>'
        f'<div style="margin-top:12px">{verdict}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Store result
    st.session_state["debate_result"] = {
        "question":     question,
        "rounds":       rounds,
        "for_args":     for_args,
        "against_args": against_args,
        "verdict":      verdict,
        "model":        debate_model,
    }

    st.success("✅ Debate complete!")

    # ── Download transcript ──────────────────────────────────────────────────
    transcript_lines = [f"# Debate: {question}\n\n"]
    for i, (f, a) in enumerate(zip(for_args, against_args), 1):
        transcript_lines.append(f"## Round {i}\n\n### FOR\n{f}\n\n### AGAINST\n{a}\n\n")
    transcript_lines.append(f"## Verdict\n{verdict}\n")
    transcript_text = "".join(transcript_lines)

    st.download_button(
        label="📥 Download Debate Transcript (Markdown)",
        data=transcript_text,
        file_name=f"debate_{question[:30].replace(' ', '_')}.md",
        mime="text/markdown",
    )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built for Hackathon 🏆 | "
    "Multi-Agent Debate System | "
    "Powered by [Ollama](https://ollama.com) + Streamlit"
)
