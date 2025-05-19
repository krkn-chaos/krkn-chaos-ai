from typing import List
from pydantic import BaseModel
from chaos_ai.models.member import BaseMember


class Population(BaseModel):
    current_population: List[BaseMember] = []
    population_size: int = 10
    