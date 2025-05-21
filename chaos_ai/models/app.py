from pydantic import BaseModel
import datetime

from chaos_ai.models.base_scenario import Scenario


class CommandRunResult(BaseModel):
    scenario: Scenario
    cmd: str
    log: str
    returncode: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    fitness_score: float
