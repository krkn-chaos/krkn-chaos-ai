from typing import List, Optional
from pydantic import BaseModel, Field


class PodScenarioConfig(BaseModel):
    namespace: List[str] = ["openshift-.*"]
    pod_label: List[str] = [""]
    name_pattern: List[str] = [".*"]


class AppOutageScenarioConfig(BaseModel):
    namespace: List[str] = []
    pod_selector: List[str] = []


class ContainerScenarioConfig(BaseModel):
    namespace: List[str] = []
    label_selector: List[str] = []
    container_name: List[str] = []


class NodeHogScenarioConfig(BaseModel):
    node_selector: List[str] = []
    taints: List[str] = []


class ScenarioConfig(BaseModel):
    application_outages: Optional[AppOutageScenarioConfig] = Field(
        alias="application-outages", default=None
    )
    pod_scenarios: Optional[PodScenarioConfig] = Field(
        alias="pod-scenarios", default=None
    )
    container_scenarios: Optional[ContainerScenarioConfig] = Field(
        alias="container-scenarios", default=None
    )
    node_cpu_hog: Optional[NodeHogScenarioConfig] = Field(
        alias="node-cpu-hog", default=None
    )
    node_memory_hog: Optional[NodeHogScenarioConfig] = Field(
        alias="node-memory-hog", default=None
    )


class ConfigFile(BaseModel):
    kubeconfig_file_path: str  # Path to kubeconfig

    generations: int = 20  # Total number of generations to run.
    population_size: int = 10  # Initial population size

    fitness_function: str  # PromQL fitness function

    scenario: ScenarioConfig = ScenarioConfig()
