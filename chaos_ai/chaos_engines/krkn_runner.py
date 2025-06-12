import os
import json
import datetime

from krkn_lib.prometheus.krkn_prometheus import KrknPrometheus
from chaos_ai.models.app import CommandRunResult, KrknRunnerType
from chaos_ai.models.config import ConfigFile, FitnessFunctionType
from chaos_ai.models.base_scenario import Scenario
from chaos_ai.utils.fs import run_shell
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# TODO: Cleanup of temp kubeconfig after running the script

PODMAN_TEMPLATE = 'podman run --env-host=true -e PUBLISH_KRAKEN_STATUS="False" -e TELEMETRY_PROMETHEUS_BACKUP="False" -e WAIT_DURATION=0 {env_list} --net=host -v {kubeconfig}:/home/krkn/.kube/config:Z containers.krkn-chaos.dev/krkn-chaos/krkn-hub:{name}'

KRKNCTL_TEMPLATE = 'krknctl run {name} --telemetry-prometheus-backup False --wait-duration 0 --kubeconfig {kubeconfig} {env_list}'

KRKN_HUB_FAILURE_SCORE = 5


class KrknRunner:
    def __init__(self, config: ConfigFile, runner_type: KrknRunnerType = KrknRunnerType.HUB_RUNNER):
        self.config = config
        self.prom_client = self.__connect_prom_client()
        self.runner_type = runner_type

    def run(self, scenario: Scenario, generation_id: int) -> CommandRunResult:
        logger.debug("Running scenario %s", scenario)

        command = self.runner_command(scenario)

        start_time = datetime.datetime.now()

        log, returncode = run_shell(command)
        # log = ""
        # returncode = 0

        end_time = datetime.datetime.now()

        fitness = self.calculate_fitness(start_time, end_time)

        # Include krkn hub run failure info to the fitness score
        if self.config.fitness_function.include_krkn_failure:
            # Status code 2 means that SLOs not met per Krkn test
            if returncode == 2:
                fitness += KRKN_HUB_FAILURE_SCORE

        return CommandRunResult(
            generation_id=generation_id,
            scenario=scenario,
            cmd=command,
            log=log,
            returncode=returncode,
            start_time=start_time,
            end_time=end_time,
            fitness_score=fitness,
        )

    def runner_command(self, scenario: Scenario):
        '''Generate command for krkn runner (krknctl, krknhub)'''
        if self.runner_type == KrknRunnerType.HUB_RUNNER:
            # Generate env items
            env_list = ""
            for parameter in scenario.parameters:
                env_list += f' -e {parameter.name}="{parameter.value}" '

            command = PODMAN_TEMPLATE.format(
                env_list=env_list,
                kubeconfig=self.config.kubeconfig_file_path,
                name=scenario.name,
            )
            return command
        elif self.runner_type == KrknRunnerType.CLI_RUNNER:
            # Generate env parameters for scenario
            # krknctl the env parameter keys are small-casing, separated by hyphens
            # by default we use upper-casing, separated by underscore.
            env_list = ""
            for parameter in scenario.parameters:
                param_name = (parameter.name).lower().replace("_", "-")
                env_list += f'--{param_name} "{parameter.value}" '

            command = KRKNCTL_TEMPLATE.format(
                env_list=env_list,
                kubeconfig=self.config.kubeconfig_file_path,
                name=scenario.name,
            )
            return command
        raise Exception("Unsupported runner type")

    def __connect_prom_client(self):
        # Fetch Prometheus query endpoint
        url = os.getenv("PROMETHEUS_URL", "")
        if url == "":
            prom_spec_json, _ = run_shell(
                f"kubectl --kubeconfig={self.config.kubeconfig_file_path} -n openshift-monitoring get route -l app.kubernetes.io/name=thanos-query -o json"
            )
            prom_spec_json = json.loads(prom_spec_json)
            url = prom_spec_json["items"][0]["spec"]["host"]

        # Fetch K8s token to access internal service
        token = os.getenv("PROMETHEUS_TOKEN", "")
        if token == "":
            token, _ = run_shell(
                f"oc --kubeconfig={self.config.kubeconfig_file_path} whoami -t",
                do_not_log=True,
            )

        logger.info("Prometheus URL: %s", url)

        return KrknPrometheus(f"https://{url}", token.strip())

    def calculate_fitness(self, start, end):
        '''Calculate fitness score for scenario run'''
        # return random.randint(0, 10)
        try:
            if self.config.fitness_function.type == FitnessFunctionType.point:
                return self.calculate_point_fitness(start, end)
            elif self.config.fitness_function.type == FitnessFunctionType.range:
                return self.calculate_range_fitness(start, end)
        except Exception as error:
            logger.error("Fitness function calculation failed: %s", error)
            raise error

    def calculate_point_fitness(self, start, end):
        '''Takes difference between fitness function at start/end intervals of test.
           Helpful to measure values for counter based metric like restarts. 
        '''
        logger.info("Calculating Point Fitness")
        result_at_beginning = self.prom_client.process_prom_query_in_range(
                self.config.fitness_function.query,
                start_time=start,
                end_time=start,
                granularity=100,
            )[0]["values"][-1][1]

        result_at_end = self.prom_client.process_prom_query_in_range(
            self.config.fitness_function.query,
            start_time=end,
            end_time=end,
            granularity=100,
        )[0]["values"][-1][1]

        return float(result_at_end) - float(result_at_beginning)

    def calculate_range_fitness(self, start, end):
        '''
        Measure fitness function for the range of test.
        Helpful to measure value over period of time like max cpu usage, max memory usage over time, etc.

        config.fitness_function.query can specify a dynamic "$range$" parameter that will be replaced
        when calling below function.
        '''
        logger.info("Calculating Range Fitness")

        query = self.config.fitness_function.query
        # Calculate number of minutes between test run

        if '$range$' in query:
            time_dt_mins = int((end - start).total_seconds() / 60)
            if time_dt_mins == 0:
                time_dt_mins = 1
            query = query.replace('$range$', f'{time_dt_mins}m')
        else:
            logger.warning("You are missing $range$ in config.fitness_function.query to specify dynamic range. Fitness function will use specified range")

        result = self.prom_client.process_prom_query_in_range(
            query,
            start_time=start,
            end_time=end,
            granularity=100,
        )[0]["values"][-1][1]

        return float(result)
