from .state import AssistantState


def route_from_planner(state: AssistantState):
    if state.get("error"):
        return "error_handler"

    step = state.get("step")
    if step == "TOOL":
        return "tool_executor"
    if step == "ANSWER":
        return "response_generator"
    return "error_handler"