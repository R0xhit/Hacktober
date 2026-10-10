# ⚔️ Multi-Agent Debate Arena

> **Hackathon Project** — Two AI agents argue opposite sides of any question. A third judge picks the winner.

## 🧠 Concept

Single LLMs suffer from:
- **Sycophancy** — they agree with whatever the user implies
- **Hallucination** — unchallenged claims go unverified
- **Hidden bias** — one perspective dominates

This project fixes that with **role-forced multi-agent debate**:

```
Question
   │
   ├─► Agent FOR  (llama3.2, forced to argue FOR)
   │      ↕ rebuttals across rounds
   └─► Agent AGAINST (llama3.2, forced to argue AGAINST)
             │
             ▼
         Judge Agent (llama3.2, impartial evaluation)
             │
             ▼
         Structured Verdict + Scores
```

## 🏗️ Architecture

| Component | File | Role |
|-----------|------|------|
| `DebaterAgent` | `agents.py` | Argues FOR or AGAINST, keeps chat history |
| `JudgeAgent` | `agents.py` | Evaluates transcript, scores, picks winner |
| `run_debate()` | `agents.py` | Orchestrates multi-round debate loop |
| Streamlit UI | `app.py` | Web interface with live updates |
| CLI | `cli.py` | Terminal interface for quick testing |

## ⚡ Quick Start

### 1. Prerequisites

- [Ollama](https://ollama.com) installed and running
- Python 3.10+

### 2. Pull a model

```bash
ollama pull llama3.2
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the web app

```bash
streamlit run app.py
```

### 5. (Optional) Run in terminal

```bash
python cli.py "Should AI be given legal personhood?" --rounds 2
```

## ⚙️ Configuration

Edit `.env` to change models or settings:

```env
DEBATE_MODEL=llama3.2      # Model for both debater agents
JUDGE_MODEL=llama3.2       # Model for the judge
DEBATE_ROUNDS=2            # Default number of rounds
OLLAMA_HOST=http://localhost:11434
```

**Try other models:**
```bash
ollama pull mistral
ollama pull qwen2.5
ollama pull phi4
```

Then set `DEBATE_MODEL=mistral` in `.env`.

## 📁 Project Structure

```
multi-agent-debate/
├── app.py              # Streamlit web UI
├── agents.py           # Core agent logic (DebaterAgent, JudgeAgent)
├── cli.py              # Terminal interface
├── requirements.txt    # Python dependencies
├── .env                # Configuration
└── README.md
```

## 🎯 Hackathon Talking Points

1. **Same model, different roles** — proves role-forcing creates diversity without needing different models
2. **Memory across rounds** — agents remember their own arguments, enabling coherent multi-round rebuttals
3. **Structured judge output** — scores provide calibrated confidence, not just a binary answer
4. **Zero API cost** — fully local with Ollama

## 🏆 Example Output

**Question:** "Should AI be given legal personhood?"

- 🟢 **FOR** argues: AI systems show goal-directed behavior, contracts should be enforceable...
- 🔴 **AGAINST** argues: Legal personhood requires moral responsibility, AI lacks consciousness...
- 👨‍⚖️ **Judge**: `WINNER: AGAINST | Score FOR: 6/10 | Score AGAINST: 8/10`
