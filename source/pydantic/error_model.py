from pydantic import BaseModel
from typing import List, Optional

class ErrorDetail(BaseModel):
    type:str
    message:str
    loc:str