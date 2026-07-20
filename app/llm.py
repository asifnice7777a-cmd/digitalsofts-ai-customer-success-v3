import json
import re
from typing import List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq

from app.config import settings
from app.logging_config import logger


_NO_REASONING_INSTRUCTION = (
    "Respond with your final answer only. Do not include your internal reasoning, "
    "chain-of-thought, planning steps, or thinking process in your reply — output only "
    "the finished message intended for the client."
)

_REASONING_BLOCK_PATTERN = re.compile(
    r"<(think|thinking|reasoning|scratchpad)>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)

# Keywords used by the manual (non-native) tool-calling fallback to decide
# whether the cost-estimation tool is relevant to a given message.
_COST_KEYWORDS = ["price", "pricing", "cost", "budget", "estimate", "quote"]

# Cached once we learn the configured model does not support native tool calling,
# so we don't repeatedly hit the failing bind_tools() call on every request.
_native_tool_calling_supported: Optional[bool] = None


def _strip_reasoning(text: Optional[str]) -> Optional[str]:
    """Remove any internal reasoning/chain-of-thought blocks a model may emit
    inside its content, so only the final answer ever reaches the user."""
    if not text:
        return text
    cleaned = _REASONING_BLOCK_PATTERN.sub("", text)
    return cleaned.strip()


def _is_tool_unsupported_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "does not support tools" in msg:
        return True
    if "400" in msg and "tool" in msg:
        return True
    return False


def get_llm(temperature: float = 0.3) -> Optional[ChatGroq]:
    """Build the chat model client, using Groq's API."""
    if not settings.GROQ_API_KEY:
        return None
    try:
        return ChatGroq(
            model=settings.MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=temperature,
        )
    except Exception as exc:
        logger.error("Failed to initialize LLM: %s", exc)
        return None


def call_llm(system_prompt: str, user_message: str, fallback: str) -> str:
    """Single-shot call with no tools."""
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        guarded_prompt = f"{_NO_REASONING_INSTRUCTION}\n\n{system_prompt}"
        response = llm.invoke([("system", guarded_prompt), ("human", user_message)])
        content = _strip_reasoning(response.content)
        return content if content else fallback
    except Exception as exc:
        logger.error("LLM call failed, using fallback: %s", exc)
        return fallback


def _call_llm_native_tools(
    llm: ChatGroq,
    system_prompt: str,
    user_message: str,
    tools: List[BaseTool],
    fallback: str,
    max_iterations: int,
) -> str:
    """Original bind_tools()-based tool-calling loop. May raise if the model
    does not support native tool calling; caller handles fallback."""
    llm_with_tools = llm.bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    guarded_prompt = f"{_NO_REASONING_INSTRUCTION}\n\n{system_prompt}"
    messages = [SystemMessage(content=guarded_prompt), HumanMessage(content=user_message)]

    for _ in range(max_iterations):
        ai_message: AIMessage = llm_with_tools.invoke(messages)
        messages.append(ai_message)

        if not ai_message.tool_calls:
            content = _strip_reasoning(ai_message.content)
            return content if content else fallback

        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool is None:
                tool_result = f"Error: tool '{tool_name}' not found."
            else:
                try:
                    tool_result = selected_tool.invoke(tool_args)
                except Exception as tool_exc:
                    logger.error("Tool '%s' execution failed: %s", tool_name, tool_exc)
                    tool_result = f"Error executing tool '{tool_name}': {tool_exc}"

            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call_id)
            )

    final = llm_with_tools.invoke(messages)
    content = _strip_reasoning(final.content)
    return content if content else fallback


def _run_manual_tool_selection(
    tools_by_name: dict,
    user_message: str,
) -> List[str]:
    """Deterministic, keyword-based tool selection used by the manual
    fallback (no JSON tool-selection round trip to the model)."""
    text = user_message.lower()
    results = []

    if "search_company_knowledge" in tools_by_name:
        selected_tool = tools_by_name["search_company_knowledge"]
        try:
            result = selected_tool.invoke({"query": user_message})
        except Exception as tool_exc:
            logger.error("Tool 'search_company_knowledge' execution failed: %s", tool_exc)
            result = f"Error executing tool 'search_company_knowledge': {tool_exc}"
        results.append(f"[search_company_knowledge] {result}")

    if "estimate_project_cost" in tools_by_name and any(k in text for k in _COST_KEYWORDS):
        selected_tool = tools_by_name["estimate_project_cost"]
        try:
            result = selected_tool.invoke({"project_description": user_message})
        except Exception as tool_exc:
            logger.error("Tool 'estimate_project_cost' execution failed: %s", tool_exc)
            result = f"Error executing tool 'estimate_project_cost': {tool_exc}"
        results.append(f"[estimate_project_cost] {result}")

    return results


def _call_llm_manual_tools(
    llm: ChatGroq,
    system_prompt: str,
    user_message: str,
    tools: List[BaseTool],
    fallback: str,
    max_iterations: int,
) -> str:
    """Fallback for models without native tool-calling support. Tool
    selection is done deterministically in Python via simple keyword rules
    instead of asking the model to choose tools through JSON. Selected tools
    are executed directly, and their results are appended to the ORIGINAL
    system_prompt — which already contains remembered context such as
    "Known client info: {...}" — rather than replacing it, so the model
    answers using both the client profile and the tool output. Only one
    final LLM call is made to produce the answer."""
    tools_by_name = {t.name: t for t in tools}
    tool_results = _run_manual_tool_selection(tools_by_name, user_message)

    if tool_results:
        tool_results_block = "\n".join(tool_results)
        final_prompt = (
            f"{_NO_REASONING_INSTRUCTION}\n\n"
            f"{system_prompt}\n\n"
            "The following additional information comes from company tools and MUST be "
            "treated as factual:\n"
            f"{tool_results_block}\n\n"
            "Answer using BOTH the remembered client profile above and the tool results "
            "above. Do not ask unnecessary clarification questions if the information "
            "already available (from the profile or the tool results) is sufficient."
        )
    else:
        final_prompt = f"{_NO_REASONING_INSTRUCTION}\n\n{system_prompt}"

    try:
        final_response = llm.invoke([
            ("system", final_prompt),
            ("human", user_message),
        ])
        content = _strip_reasoning(final_response.content)
        return content if content else fallback
    except Exception as exc:
        logger.error("LLM manual tool-calling final call failed, using fallback: %s", exc)
        return fallback


def call_llm_with_tools(
    system_prompt: str,
    user_message: str,
    tools: List[BaseTool],
    fallback: str,
    max_iterations: int = 5,
) -> str:
    """
    Lets the LLM decide whether, which, and how many tools to call.
    Python only executes the tool calls the LLM requests and returns the
    results back to the LLM — no business logic here decides tool selection.

    If the underlying model does not support native tool calling, this
    transparently falls back to a manual tool-selection loop that achieves
    the same behavior via plain prompting, using the exact same tools.
    """
    llm = get_llm()
    if llm is None:
        return fallback

    global _native_tool_calling_supported

    if not tools:
        return call_llm(system_prompt, user_message, fallback)

    if _native_tool_calling_supported is not False:
        try:
            return _call_llm_native_tools(llm, system_prompt, user_message, tools, fallback, max_iterations)
        except Exception as exc:
            if _is_tool_unsupported_error(exc):
                logger.warning(
                    "Model '%s' does not support native tool calling; falling back to manual tool execution.",
                    settings.MODEL_NAME,
                )
                _native_tool_calling_supported = False
            else:
                logger.error("LLM tool-calling call failed, using fallback: %s", exc)
                return fallback

    return _call_llm_manual_tools(llm, system_prompt, user_message, tools, fallback, max_iterations)