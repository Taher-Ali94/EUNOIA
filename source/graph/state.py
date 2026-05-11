from typing import Any, Literal,Optional
from typing_extensions import TypedDict
from typing import Annotated
from operator import add


class AssistantState(TypedDict, total=False):
    messages: Annotated[list[dict[str, str]], add]
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