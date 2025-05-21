import random
from typing import List
from pydantic import BaseModel
import chaos_ai.models.base_scenario_parameter as param
from chaos_ai.models.config import ConfigFile
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)


class Scenario(BaseModel):
    name: str
    parameters: List[param.BaseParameter]

    def __str__(self):
        param_value = ", ".join([str(x.value) for x in self.parameters])
        return f"{self.name}({param_value})"


class ScenarioFactory:
    @staticmethod
    def generate_random_scenario(
        config: ConfigFile,
    ):
        scenario = random.choice(['pod-scenarios', 'application-outages'])
        try:
            if scenario == 'pod-scenarios':
                return ScenarioFactory.create_pod_scenario(
                    **config.scenario.pod_scenarios.model_dump()
                )
            elif scenario == 'application-outages':
                return ScenarioFactory.create_application_outage_scenario(
                    **config.scenario.application_outages.model_dump()
                )
        except Exception as error:
            logger.error("Unable to generate scenario: %s", error)

    @staticmethod
    def create_pod_scenario(
        namespace: List[str] = ["openshift-.*"],
        pod_label: List[str] = [""],
        name_pattern: List[str] = [".*"],
    ):
        return Scenario(
            name="pod-scenarios",
            parameters=[
                param.NamespaceParameter(
                    possible_values=namespace,
                    value=random.choice(namespace),
                ),
                param.PodLabelParameter(
                    possible_values=pod_label,
                    value=random.choice(pod_label),
                ),
                param.NamePatternParameter(
                    possible_values=name_pattern,
                    value=random.choice(name_pattern),
                ),
                param.DisruptionCountParameter(),
                param.KillTimeoutParameter(),
                param.ExpRecoveryTimeParameter(),
            ],
        )

    @staticmethod
    def create_application_outage_scenario(
        namespace: List[str],
        pod_selector: List[str],
    ):
        return Scenario(
            name="application-outages",
            parameters=[
                param.DurationParameter(),
                param.NamespaceParameter(
                    possible_values=namespace,
                    value=random.choice(namespace),
                ),
                param.PodSelectorParameter(
                    possible_values=pod_selector,
                    value=random.choice(pod_selector),
                ),
                param.BlockTrafficType(),
            ]
        )
