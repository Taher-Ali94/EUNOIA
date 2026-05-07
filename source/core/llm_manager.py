from ollama import Client
from ..pydantic.llm_response_model import LLMResponse
from pydantic import ValidationError
from json import JSONDecodeError

class LLMManager:
    def __init__(self,model_name:str = "Eunoia",keep_alive:str="10m"
                 ,num_predict:int=100,temperature:float=0):
        self.client = Client()
        self.model_name = model_name
        self.keep_alive = keep_alive
        self.num_predict = num_predict
        self.temperature = temperature
        self.output = None 

    def call_llm(self,messages=list):
        response = self.client.chat(
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

        raw = response["message"]["content"]

        try:
            self.output = LLMResponse.model_validate_json(raw)
        except Exception as e:
            print("Error parsing LLM response:", e)
        except ValidationError as e:
                print(f"Pydantic validation failed: {e}")
        except JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            self.output = None

        return self.output , raw
    
    def wake_llm(self):
        return self.call_llm(
            [
                {
                    "role": "user",
                    "content": "greet the user by their name and ask how you can assist them today.",
                }
            ]
        )


