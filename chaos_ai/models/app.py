from pydantic import BaseModel
import datetime
from enum import Enum
from typing import List

from chaos_ai.models.base_scenario import BaseScenario


class FitnessScoreResult(BaseModel):
    id: int
    fitness_score: float
    weighted_score: float


class FitnessResult(BaseModel):
    scores: List[FitnessScoreResult] = []
    fitness_score: float = 0.0    # Overall fitness score


class CommandRunResult(BaseModel):
    generation_id: int      # Which generation was scenario referred
    scenario: BaseScenario  # scenario details
    cmd: str                # Krkn-Hub command 
    log: str                # Log details or path to log file
    returncode: int         # Return code of Krkn-Hub scenario execution
    start_time: datetime.datetime   # Start date timestamp of the test 
    end_time: datetime.datetime     # End date timestamp of the test
    fitness_result: FitnessResult   # Fitness result measured for scenario.


class KrknRunnerType(str, Enum):
    HUB_RUNNER = "HUB_RUNNER"
    CLI_RUNNER = "CLI_RUNNER"
