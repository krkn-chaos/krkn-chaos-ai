import random

from typing import List
from pydantic import BaseModel


class BaseParameter(BaseModel):
    name: str


class NamespaceParameter(BaseParameter):
    name: str = "NAMESPACE"
    value: str = "openshift-.*"
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class PodLabelParameter(BaseParameter):
    name: str = "POD_LABEL"
    value: str = ""  # Example: service=payment
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class NamePatternParameter(BaseParameter):
    name: str = "NAME_PATTERN"
    value: str = ".*"
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class DisruptionCountParameter(BaseParameter):
    name: str = "DISRUPTION_COUNT"
    value: int = 1
    max_value: int = 25  # some arbitrary value

    def mutate(self):
        self.value = random.randint(1, self.max_value)


class KillTimeoutParameter(BaseParameter):
    name: str = "KILL_TIMEOUT"
    value: int = 120

    def mutate(self):
        self.value = self.value


class ExpRecoveryTimeParameter(BaseParameter):
    name: str = "EXPECTED_RECOVERY_TIME"
    value: int = 60

    def mutate(self):
        pass


class DurationParameter(BaseParameter):
    name: str = "DURATION"
    value: int = 120

    def mutate(self):
        if random.random() < 0.5:
            self.value += random.randint(1, 15) * self.value / 100
        else:
            self.value -= random.randint(1, 15) * self.value / 100
        self.value = max(self.value, 10)
        self.value = min(self.value, 600)


class PodSelectorParameter(BaseParameter):
    name: str = "POD_SELECTOR"
    value: str
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class BlockTrafficType(BaseParameter):
    name: str = "BLOCK_TRAFFIC_TYPE"
    value: str = "[Ingress, Egress]"
    possible_values: List[str] = ["[Ingress, Egress]", "[Ingress]", "[Egress]"]

    def mutate(self):
        self.value = random.choice(self.possible_values)


class LabelSelectorParameter(BaseParameter):
    name: str = "LABEL_SELECTOR"
    value: str  # Example Value: k8s-app=etcd
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class ContainerNameParameter(BaseParameter):
    name: str = "CONTAINER_NAME"
    value: str  # Example Value: etcd
    possible_values: List[str] = []

    def mutate(self):
        self.value = random.choice(self.possible_values)


class ActionParameter(BaseParameter):
    name: str = "ACTION"
    value: str = "1"
    possible_values: List[str] = ["1", "9"]

    def mutate(self):
        self.value = random.choice(self.possible_values)
