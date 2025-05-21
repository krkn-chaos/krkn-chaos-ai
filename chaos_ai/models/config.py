from typing import List
from pydantic import BaseModel, Field


class PodScenarioConfig(BaseModel):
    namespace: List[str] = ["openshift-.*"]
    pod_label: List[str] = [""]
    name_pattern: List[str] = [".*"]


class AppOutageScenarioConfig(BaseModel):
    namespace: List[str] = []
    pod_selector: List[str] = []


class ScenarioConfig(BaseModel):
    application_outages: AppOutageScenarioConfig = Field(alias='application-outages')
    pod_scenarios: PodScenarioConfig = Field(alias='pod-scenarios')


class ConfigFile(BaseModel):
    kubeconfig_file_path: str  # Path to kubeconfig

    generations: int = 20  # Total number of generations to run.
    population_size: int = 10  # Initial population size

    fitness_function: str  # PromQL fitness function

    scenario: ScenarioConfig
