from typing import List
from pydantic import BaseModel


class ConfigFile(BaseModel):
    max_generation_count: int = 20
    population_size: int = 10

    reward_function_query: str
    