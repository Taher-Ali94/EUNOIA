from typing import Any, Literal,Optional
from typing_extensions import NotRequired, TypedDict


class AssistantState(TypedDict, total=False):
    messages: list[dict[str, str]]
    current_user_input: str
    step: Literal["THINK", "TOOL", "OBSERVE", "ANSWER"]

    tool_name: Optional[str | None]
    tool_input: Optional[str | None]
    tool_result: Optional[Any]

    memory_hits: Optional[list[dict[str, Any]]]
    user_profile: Optional[dict[str, Any]]
    error: Optional[str | None]
    final_response: Optional[str | None]

    llm_output_raw: Optional[str | None]
    reasoning_steps: Optional[int]