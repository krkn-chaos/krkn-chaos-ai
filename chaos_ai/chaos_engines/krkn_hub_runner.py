import json
import datetime

from krkn_lib.prometheus.krkn_prometheus import KrknPrometheus
from chaos_ai.models.app import CommandRunResult
from chaos_ai.models.config import ConfigFile
from chaos_ai.models.base_scenario import Scenario
from chaos_ai.utils.fs import run_shell
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)


PODMAN_TEMPLATE = 'podman run --env-host=true -e TELEMETRY_PROMETHEUS_BACKUP="False" -e WAIT_DURATION=0 {env_list} --net=host -v {kubeconfig}:/home/krkn/.kube/config:Z containers.krkn-chaos.dev/krkn-chaos/krkn-hub:{name}'


class KrknHubRunner:
    def __init__(self, config: ConfigFile):
        self.config = config
        self.prom_client = self.__connect_prom_client()

    def run(self, scenario: Scenario) -> CommandRunResult:
        logger.debug("Running scenario %s", scenario)

        # Generate env items
        env_list = ""
        for parameter in scenario.parameters:
            env_list += f' -e {parameter.name}="{parameter.value}" '

        command = PODMAN_TEMPLATE.format(
            env_list=env_list,
            kubeconfig=self.config.kubeconfig_file_path,
            name=scenario.name
        )

        start_time = datetime.datetime.now()

        log, returncode = run_shell(command)

        end_time = datetime.datetime.now()

        return CommandRunResult(
            scenario=scenario,
            cmd=command,
            log=log,
            returncode=returncode,
            start_time=start_time,
            end_time=end_time,
            fitness_score=self.calculate_fitness(start_time, end_time)
        )

    def __connect_prom_client(self):
        # | jq --raw-output '.items[0].spec.host'
        prom_spec_json, _ = run_shell(
            f"kubectl --kubeconfig={self.config.kubeconfig_file_path} -n openshift-monitoring get route -l app.kubernetes.io/name=thanos-query -o json"
        )
        prom_spec_json = json.loads(prom_spec_json)
        url = prom_spec_json['items'][0]['spec']['host']

        token, _ = run_shell(
            "oc whoami -t"
        )
        logger.info("Prometheus URL: %s", url)
        # logger.info("Token: %s", token)

        return KrknPrometheus(f"https://{url}", token.strip)

    def calculate_fitness(self, start, end):
        try:
            result_at_beginning = self.prom_client.process_prom_query_in_range(
                self.config.fitness_function,
                start_time=start,
                end_time=start,
                granularity=100
            )[0]['values'][-1][1]

            result_at_end = self.prom_client.process_prom_query_in_range(
                self.config.fitness_function,
                start_time=end,
                end_time=end,
                granularity=100
            )[0]['values'][-1][1]

            return float(result_at_end) - float(result_at_beginning)
        except Exception as error:
            logger.error("Fitness function calculation failed: %s", error)
            raise error
