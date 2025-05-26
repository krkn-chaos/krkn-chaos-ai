import random
from typing import List
from pydantic import BaseModel
import chaos_ai.models.base_scenario_parameter as param
from chaos_ai.models.config import ConfigFile
from chaos_ai.models.custom_errors import EmptyConfigError
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)


class Scenario(BaseModel):
    name: str
    parameters: List[param.BaseParameter]

    def __str__(self):
        param_value = ", ".join([str(x.value) for x in self.parameters])
        return f"{self.name}({param_value})"

    def __eq__(self, other):
        if not isinstance(other, Scenario):
            return NotImplemented
        self_params = ", ".join([str(x.value) for x in self.parameters])
        other_params = ", ".join([str(x.value) for x in other.parameters])
        return self.name == other.name and self_params == other_params

    def __hash__(self):
        self_params = ", ".join([str(x.value) for x in self.parameters])
        return hash((self.name, self_params))


class ScenarioFactory:
    @staticmethod
    def generate_random_scenario(
        config: ConfigFile,
    ):
        # Pick random available choice to try
        choices = []

        if config.scenario.pod_scenarios is not None:
            choices.append("pod-scenarios")
        elif config.scenario.application_outages is not None:
            choices.append("application-outages")
        elif config.scenario.container_scenarios is not None:
            choices.append("container-scenarios")
        elif config.scenario.node_cpu_hog is not None:
            choices.append("node-cpu-hog")

        if len(choices) == 0:
            raise EmptyConfigError(
                "No scenarios found. Please provide atleast 1 scenario."
            )

        scenario = random.choice(choices)

        try:
            if (
                scenario == "pod-scenarios"
                and config.scenario.pod_scenarios is not None
            ):
                return ScenarioFactory.create_pod_scenario(
                    **config.scenario.pod_scenarios.model_dump()
                )
            elif (
                scenario == "application-outages"
                and config.scenario.application_outages is not None
            ):
                return ScenarioFactory.create_application_outage_scenario(
                    **config.scenario.application_outages.model_dump()
                )
            elif (
                scenario == "container-scenarios"
                and config.scenario.container_scenarios is not None
            ):
                return ScenarioFactory.create_container_scenario(
                    **config.scenario.container_scenarios.model_dump()
                )
            elif (
                scenario == "node-cpu-hog" and config.scenario.node_cpu_hog is not None
            ):
                return ScenarioFactory.create_cpu_hog_scenario(
                    **config.scenario.node_cpu_hog.model_dump()
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
            ],
        )

    @staticmethod
    def create_container_scenario(
        namespace: List[str], label_selector: List[str], container_name: List[str]
    ):
        return Scenario(
            name="container-scenarios",
            parameters=[
                param.NamespaceParameter(
                    possible_values=namespace,
                    value=random.choice(namespace),
                ),
                param.LabelSelectorParameter(
                    possible_values=label_selector,
                    value=random.choice(label_selector),
                ),
                param.DisruptionCountParameter(),
                param.ContainerNameParameter(
                    possible_values=container_name, value=random.choice(container_name)
                ),
                param.ActionParameter(),
                param.ExpRecoveryTimeParameter(),
            ],
        )

    @staticmethod
    def create_cpu_hog_scenario(node_selector: List[str], taints: List[str]):
        return Scenario(
            name="node-cpu-hog",
            parameters=[
                param.TotalChaosDurationParameter(),
                param.NodeCPUCoreParameter(),
                param.NodeCPUPercentageParameter(),
                param.NamespaceParameter(value="default", possible_values=["default"]),
                param.NodeSelectorParameter(
                    possible_values=node_selector, value=random.choice(node_selector)
                ),
                param.TaintParameter(possible_values=taints, value=random.choice(taints)),
                param.NumberOfNodesParameter(),
                param.CPUHogImageParameter(),
            ],
        )
