"""
AI agent that, given a candidate profile, drafts a personalized email
requesting PAN and Aadhaar for background verification.

We expose two tools to the LLM:
  - draft_message: compose the subject + body
  - log_request:   persist the recipient (this is the "send" stand-in)

In a real system `log_request` would be replaced by the email-provider call.
"""
import json
from typing import Optional, Dict, Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from ..config import get_llm_provider, OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL


# The agent fills this dict in place; we read it back after the run.
# Module-level mutable state is a bit ugly but keeps the tool signatures
# clean for the LLM to call.
_run_state: Dict[str, Any] = {}


@tool
def draft_message(subject: str, body: str) -> str:
    """Save a draft outreach email. Returns a confirmation string."""
    _run_state["draft"] = {
        "subject": subject.strip() if subject else None,
        "body": body.strip(),
    }
    return "draft saved"


@tool
def log_request(recipient: str) -> str:
    """Log the outreach as sent. Use after draft_message.
    `recipient` is the candidate's email address."""
    _run_state["logged"] = {"recipient": recipient.strip()}
    return "logged"


def run_document_request_agent(candidate: dict) -> dict:
    """
    Returns a dict like:
      {recipient, subject, message}
    """
    provider = get_llm_provider()
    if not provider:
        return _fallback_compose(candidate)

    _run_state.clear()

    try:
        llm = _build_llm(provider)
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an HR assistant at TraqCheck. Your job: write a courteous, "
             "personalized email asking the candidate to share their PAN and Aadhaar "
             "documents for background verification.\n\n"
             "Tone: warm, professional, 4-7 sentences. Include a clear subject line, "
             "mention how to share (reply with attachments, both sides clearly visible, "
             "etc.), and sign off as 'TraqCheck HR'. Greet the candidate by their first "
             "name when available, and reference their role/company when relevant.\n\n"
             "Workflow: call `draft_message` first with subject and body, then "
             "`log_request` with the candidate's email."),
            ("human", "Candidate JSON:\n{candidate_json}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        tools = [draft_message, log_request]
        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=4)

        executor.invoke({"candidate_json": json.dumps(_minify(candidate))})

        draft = _run_state.get("draft") or {}
        logged = _run_state.get("logged") or {}

        recipient = logged.get("recipient") or candidate.get("email")
        message = draft.get("body")

        if not message:
            return _fallback_compose(candidate)

        return {
            "recipient": recipient,
            "subject": draft.get("subject"),
            "message": message,
        }
    except Exception as e:
        out = _fallback_compose(candidate)
        out["error"] = str(e)
        return out


def _build_llm(provider: str):
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL or "gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=0.4,
        )
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=LLM_MODEL or "claude-haiku-4-5-20251001",
        api_key=ANTHROPIC_API_KEY,
        temperature=0.4,
    )


def _minify(c: dict) -> dict:
    keys = ("name", "email", "company", "designation", "skills")
    return {k: c.get(k) for k in keys}


def _fallback_compose(c: dict) -> dict:
    """Used when no LLM key is configured, or the agent errors out."""
    first = (c.get("name") or "there").split()[0]
    role_hint = ""
    if c.get("designation") and c.get("company"):
        role_hint = f" for the {c['designation']} role at {c['company']}"
    elif c.get("company"):
        role_hint = f" for the role at {c['company']}"

    subject = "Document verification - PAN & Aadhaar"
    body = (
        f"Hi {first},\n\n"
        f"Thanks for sharing your resume{role_hint}. As part of our background "
        "verification, could you please share scanned copies (front and back where "
        "applicable) of your PAN card and Aadhaar card?\n\n"
        "You can reply to this email with both attached, or upload them through the "
        "secure link our team will share with you.\n\n"
        "Please ensure both sides are clearly visible and the corners aren't cropped.\n\n"
        "Best regards,\n"
        "TraqCheck HR"
    )
    return {"recipient": c.get("email"), "subject": subject, "message": body}
