"""
agents.py – Core debate agent logic (model-agnostic, works with any Ollama model)

Three roles:
  • DebaterAgent  – Argues FOR or AGAINST a position
  • JudgeAgent    – Evaluates both sides and picks the stronger argument
"""

import os
import ollama
from dotenv import load_dotenv

load_dotenv()

DEBATE_MODEL = os.getenv("DEBATE_MODEL", "llama3.2")
JUDGE_MODEL  = os.getenv("JUDGE_MODEL",  "llama3.2")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")

# ── shared Ollama client ───────────────────────────────────────────────────────
_client = ollama.Client(host=OLLAMA_HOST)


def _chat(model: str, messages: list[dict], stream: bool = False):
    """Thin wrapper around ollama chat; returns generator or full response."""
    return _client.chat(model=model, messages=messages, stream=stream)


# ──────────────────────────────────────────────────────────────────────────────
# Debater Agent
# ──────────────────────────────────────────────────────────────────────────────

DEBATER_SYSTEM = """You are a skilled debate agent. You will be assigned a side \
(FOR or AGAINST) on a question and must argue that position persuasively, \
using logic, evidence, and clear reasoning.

Rules:
- Stay strictly on your assigned side even if you personally disagree.
- Cite plausible examples or analogies to strengthen your points.
- Keep each response focused: 3-5 strong, distinct arguments.
- Respond only with your argument. No meta-commentary.
- You may rebut the opponent's previous point if provided.
"""


class DebaterAgent:
    """An LLM agent that argues one side of a debate."""

    def __init__(self, side: str, model: str = DEBATE_MODEL):
        """
        Args:
            side: 'FOR' or 'AGAINST'
            model: Ollama model name
        """
        if side not in ("FOR", "AGAINST"):
            raise ValueError("side must be 'FOR' or 'AGAINST'")
        self.side = side
        self.model = model
        self.history: list[dict] = [{"role": "system", "content": DEBATER_SYSTEM}]

    def argue(self, question: str, opponent_last_arg: str = "", round_num: int = 1) -> str:
        """
        Produce an argument for/against the question.

        Args:
            question: The debate topic/question.
            opponent_last_arg: The opponent's most recent argument (for rebuttals).
            round_num: Current debate round number.

        Returns:
            The debater's argument as a string.
        """
        if round_num == 1:
            user_msg = (
                f"Question: {question}\n\n"
                f"You are arguing {self.side} this position.\n"
                f"Present your opening arguments."
            )
        else:
            user_msg = (
                f"Question: {question}\n\n"
                f"You are arguing {self.side} this position.\n"
                f"Round {round_num}: The opponent just argued:\n\n"
                f"{opponent_last_arg}\n\n"
                f"Rebut their points and reinforce your position."
            )

        self.history.append({"role": "user", "content": user_msg})
        response = _chat(self.model, self.history)
        reply = response.message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply


# ──────────────────────────────────────────────────────────────────────────────
# Judge Agent
# ──────────────────────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are an impartial AI debate judge. Your role is to evaluate \
two competing arguments on a topic and determine which side presented the stronger case.

Evaluation criteria:
1. Logical coherence – Are the arguments internally consistent?
2. Evidence quality  – Are examples/analogies plausible and relevant?
3. Persuasiveness    – Would a neutral audience find this convincing?
4. Rebuttal strength – Did they effectively counter the opponent?

Output format (ALWAYS follow this exactly):
---
**WINNER**: [FOR | AGAINST | TIE]

**Score FOR**: X/10
**Score AGAINST**: X/10

**Reasoning**:
[2-4 sentences explaining your verdict]

**Key Insight**:
[One sentence on the most important thing this debate revealed about the topic]
---
"""


class JudgeAgent:
    """An LLM agent that judges a completed debate and picks the winner."""

    def __init__(self, model: str = JUDGE_MODEL):
        self.model = model

    def judge(
        self,
        question: str,
        for_arguments: list[str],
        against_arguments: list[str],
    ) -> str:
        """
        Evaluate the full debate transcript and return a verdict.

        Args:
            question: The original debate question.
            for_arguments: List of arguments made by the FOR side (one per round).
            against_arguments: List of arguments made by the AGAINST side.

        Returns:
            Structured verdict string.
        """
        # Build a readable transcript
        transcript_parts = [f"**Debate Topic:** {question}\n"]
        for i, (f_arg, a_arg) in enumerate(zip(for_arguments, against_arguments), 1):
            transcript_parts.append(f"--- Round {i} ---")
            transcript_parts.append(f"**FOR side:**\n{f_arg}")
            transcript_parts.append(f"**AGAINST side:**\n{a_arg}")
        transcript = "\n\n".join(transcript_parts)

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Here is the full debate transcript:\n\n{transcript}\n\n"
                    "Please evaluate and provide your verdict."
                ),
            },
        ]

        response = _chat(self.model, messages)
        return response.message.content


# ──────────────────────────────────────────────────────────────────────────────
# Debate Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def run_debate(question: str, rounds: int = 2) -> dict:
    """
    Run a full multi-agent debate and return all data.

    Returns a dict with keys:
        question, rounds, for_args, against_args, verdict
    """
    for_agent     = DebaterAgent("FOR")
    against_agent = DebaterAgent("AGAINST")
    judge         = JudgeAgent()

    for_args:     list[str] = []
    against_args: list[str] = []

    for r in range(1, rounds + 1):
        # FOR argues first; AGAINST can rebut in round 2+
        for_last     = for_args[-1]     if for_args     else ""
        against_last = against_args[-1] if against_args else ""

        f_arg = for_agent.argue(question, against_last, round_num=r)
        a_arg = against_agent.argue(question, for_last, round_num=r)

        for_args.append(f_arg)
        against_args.append(a_arg)

    verdict = judge.judge(question, for_args, against_args)

    return {
        "question":     question,
        "rounds":       rounds,
        "for_args":     for_args,
        "against_args": against_args,
        "verdict":      verdict,
    }
