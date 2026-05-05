from pydantic import BaseModel,Field
from typing import Optional,Literal

class LLMResponse(BaseModel):
    step: Literal["THINK", "TOOL", "ANSWER", "OBSERVE"] = Field(..., description="The current step in the process")
    content: str = Field(..., description="The content of the response for the current step")
    tool: Optional[str] = Field(None, description="The name of the tool to be used if the step is TOOL")
    tool_input: Optional[str] = Field(None, description="The input for the tool if the step is TOOL")