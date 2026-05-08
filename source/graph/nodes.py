import json
from ..core.llm_manager import LLMManager
from ..tools.registry import ToolRegistry
from .state import AssistantState
from ..memory.long_term_mem0.mem_client import MemoryClient


class AssistantNodes:
    def __init__(self, llm_manager: LLMManager, tool_registry: ToolRegistry, memory_client: MemoryClient, max_reasoning_steps: int = 5):
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        self.memory_client = memory_client
        self.max_reasoning_steps = max_reasoning_steps


    def ingest_input(self, state: AssistantState):
        messages = list(state.get("messages", []))
        user_input = state.get("current_user_input", "").strip()

        if user_input:
            messages.append({"role": "user", "content": user_input})

        return {
            "messages": messages,
            "current_user_input": user_input,
            "step": "THINK",
            "tool_name": None,
            "tool_input": None,
            "tool_result": None,
            "error": None,
            "final_response": None,
            "reasoning_steps": 0,
        }
    
    async def retrieve_memory(self, state: AssistantState):
        if self.memory_client is None:
            return {"memory_hits": []}
        
        query = state.get("current_user_input", "").strip()

        if not query:
            return {"memory_hits": []}
        
        try:
            hits = await self.memory_client.search_memory(query=query, limit=5)
            return {"memory_hits": hits}
        except Exception as e:
            return {"memory_hits": [], "error": f"Memory retrieval error: {e}"}
        
    def build_llm_messages(self, state: AssistantState):
        messages = list(state.get("messages", []))
        memory_hits = state.get("memory_hits", [])

        if memory_hits:
            message_summary = json.dumps(memory_hits, ensure_ascii=False)
            messages.append({"role": "system", "content": f"Relevant memories:\n{message_summary}"})
        
        return messages
    
    async def planner(self, state: AssistantState):
        llm_messages = self.build_llm_messages(state)
        llm_messages_scratch = list(llm_messages)
        max_steps = max(1, self.max_reasoning_steps)
        reasoning_steps = 0
        final_raw = "" 

        while reasoning_steps < max_steps:
            reasoning_steps += 1
            parsed , raw = await self.llm_manager.call_llm(llm_messages_scratch)
            final_raw = raw

            if parsed is None:
                return {
                    "error": "Failed to parse LLM response.",
                    "llm_output_raw": raw,
                    "reasoning_steps": reasoning_steps,
                }
            
            step = parsed.step
            if step in ("TOOL", "ANSWER"):
                return {
                    "step": step,
                    "tool_name": parsed.tool,
                    "tool_input": parsed.tool_input,
                    "final_response": parsed.content if step == "ANSWER" else None,
                    "llm_output_raw": final_raw,
                    "reasoning_steps": reasoning_steps,
                }
            
            llm_messages_scratch.append({"role": "assistant", "content": raw})
            llm_messages_scratch.append({"role": "user", "content": "Continue and return either TOOL or ANSWER as the next valid step."})

        return {
            "error": "Planner exceeded max reasoning steps without TOOL/ANSWER.",
            "llm_output_raw": final_raw,
            "reasoning_steps": reasoning_steps,
        }
    
    def observe_and_replan(self, state: AssistantState):
        messages = list(state.get("messages", []))
        tool_name = state.get("tool_name")
        tool_input = state.get("tool_input")
        tool_result = state.get("tool_result")
        serialized_result = json.dumps(tool_result, ensure_ascii=False)

        messages.append(
            {
                "role": "user",
                "content": f"Tool {tool_name} was called with input: {tool_input} and returned result: {serialized_result}.Use this information to continue and provide the next steps or final answer if ready.",
            }
        )

        return {
            "messages": messages,
            "step": "THINK",
            "tool_name": None,
            "tool_input": None,
        }
    
    async def tool_executor(self, state: AssistantState):
        tool_name = state.get("tool_name")
        if not tool_name:
            return {"error": "No tool selected by planner."}

        try:
            result = await self.tool_registry.execute(tool_name, state.get("tool_input"))
            return {
                "tool_result": result,
                "step": "OBSERVE",
                "error": None,
            }
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}
    
    def response_generator(self, state: AssistantState) -> AssistantState:
        final = state.get("final_response")
        if not final:
            final = "I ran into an issue generating a response."

        messages = list(state.get("messages", []))
        messages.append({"role": "assistant", "content": final})
        return {"messages": messages, "final_response": final}
    
    async def memory_updater(self, state: AssistantState):
        if self.memory_client is None:
            return {}
        
        user_text = state.get("current_user_input", "").strip()
        assistant_response = state.get("final_response", "").strip()

        if not user_text or not assistant_response:
            return {}
        
        try:
            await self.memory_client.add_memory(
                [
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_response}
                ]
            )

        except Exception as e:
            return {}
        
        return {}
    
    def error_handler(self, state: AssistantState) -> AssistantState:
        message = state.get("error") or "Unknown error."
        final = f"Sorry, I hit an error: {message}"
        messages = list(state.get("messages", []))
        messages.append({"role": "assistant", "content": final})
        return {"final_response": final, "messages": messages}


        
