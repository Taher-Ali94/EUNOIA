from ollama import AsyncClient as Client
from ..pydantic.llm_response_model import LLMResponse
from pydantic import ValidationError
from json import JSONDecodeError

class LLMManager:
    def __init__(self,model_name:str = "Eunoia",keep_alive:str="10m"
                 ,num_predict:int=200,temperature:float=0):
        self.client = Client()
        self.model_name = model_name
        self.keep_alive = keep_alive
        self.num_predict = num_predict
        self.temperature = temperature
        self.output = None 

    async def call_llm(self,messages=list[dict[str, str]]):
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=messages,
                keep_alive=self.keep_alive,
                options={
                    "num_predict": self.num_predict,
                    "temperature": self.temperature,
                },
                stream=False,
                format=LLMResponse.model_json_schema()
            )
        except Exception as e:
            print(f"Error calling LLM: {e}")
            self.output = None
            return self.output, ""

        raw = response["message"]["content"]
        print(raw)

        try:
            self.output = LLMResponse.model_validate_json(raw)
        except (ValidationError, JSONDecodeError, Exception) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw LLM output: {raw}")
            self.output = None

        return self.output , raw
    
    async def wake_llm(self):
        return  await self.call_llm(
            [
                {
                    "role": "user",
                    "content": "greet the user by their name and ask how you can assist them today.",
                }
            ]
        )


