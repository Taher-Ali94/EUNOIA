from langgraph.graph import END, START, StateGraph
from .nodes import AssistantNodes
from .router import route_from_planner
from .state import AssistantState


def build_graph(nodes: AssistantNodes):
    graph_builder = StateGraph(AssistantState)

    graph_builder.add_node("ingest_input", nodes.ingest_input)
    graph_builder.add_node("retrieve_memory", nodes.retrieve_memory)
    graph_builder.add_node("planner", nodes.planner)
    graph_builder.add_node("tool_executor", nodes.tool_executor)
    graph_builder.add_node("observe_and_replan", nodes.observe_and_replan)
    graph_builder.add_node("response_generator", nodes.response_generator)
    graph_builder.add_node("memory_updater", nodes.memory_updater)
    graph_builder.add_node("error_handler", nodes.error_handler)

    graph_builder.add_edge(START, "ingest_input")
    graph_builder.add_edge("ingest_input", "retrieve_memory")
    graph_builder.add_edge("retrieve_memory", "planner")

    graph_builder.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "tool_executor": "tool_executor",
            "response_generator": "response_generator",
            "error_handler": "error_handler",
        },
    )

    graph_builder.add_edge("tool_executor", "observe_and_replan")
    graph_builder.add_edge("observe_and_replan", "planner")

    graph_builder.add_edge("response_generator", "memory_updater")
    graph_builder.add_edge("memory_updater", END)

    graph_builder.add_edge("error_handler", END)

    return graph_builder