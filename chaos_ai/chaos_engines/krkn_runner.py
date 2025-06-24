import os
import json
import datetime
import tempfile

from krkn_lib.prometheus.krkn_prometheus import KrknPrometheus
from chaos_ai.models.app import CommandRunResult, KrknRunnerType
from chaos_ai.models.config import ConfigFile, FitnessFunctionType
from chaos_ai.models.base_scenario import (
    Scenario,
    BaseScenario,
    CompositeScenario,
    CompositeDependency,
    ScenarioFactory
)
from chaos_ai.utils.fs import run_shell
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# TODO: Cleanup of temp kubeconfig after running the script

PODMAN_TEMPLATE = 'podman run --env-host=true -e PUBLISH_KRAKEN_STATUS="False" -e TELEMETRY_PROMETHEUS_BACKUP="False" -e WAIT_DURATION=0 {env_list} --net=host -v {kubeconfig}:/home/krkn/.kube/config:Z containers.krkn-chaos.dev/krkn-chaos/krkn-hub:{name}'

KRKNCTL_TEMPLATE = "krknctl run {name} --telemetry-prometheus-backup False --wait-duration 0 --kubeconfig {kubeconfig} {env_list}"

KRKNCTL_GRAPH_RUN_TEMPLATE = "krknctl graph run {path} --kubeconfig {kubeconfig}"

KRKN_HUB_FAILURE_SCORE = 5


class KrknRunner:
    def __init__(
        self,
        config: ConfigFile,
        output_dir: str,
        runner_type: KrknRunnerType = KrknRunnerType.HUB_RUNNER,
    ):
        self.config = config
        self.prom_client = self.__connect_prom_client()
        self.runner_type = runner_type
        self.output_dir = output_dir

    def run(self, scenario: BaseScenario, generation_id: int) -> CommandRunResult:
        logger.debug("Running scenario %s", scenario)

        start_time = datetime.datetime.now()

        # Generate command krkn executor command
        log, returncode = None, None
        command = ""
        if isinstance(scenario, CompositeScenario):
            command = self.graph_command(scenario)
        elif isinstance(scenario, Scenario):
            command = self.runner_command(scenario)
        else:
            raise NotImplementedError("Scenario unable to run")

        # Run command and fetch result
        # TODO: How to capture logs from composite run scenario 
        log, returncode = run_shell(command)
        # if isinstance(scenario, CompositeScenario):
        #     log, returncode = run_shell(command)
        # else:
        #     log, returncode = "", 0

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
        """Generate command for krkn runner (krknctl, krknhub)"""
        if self.runner_type == KrknRunnerType.HUB_RUNNER:
            # Generate env items
            env_list = ""
            for parameter in scenario.parameters:
                env_list += f' -e {parameter.name}="{parameter.get_value()}" '

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
                env_list += f'--{param_name} "{parameter.get_value()}" '

            command = KRKNCTL_TEMPLATE.format(
                env_list=env_list,
                kubeconfig=self.config.kubeconfig_file_path,
                name=scenario.name,
            )
            return command
        raise Exception("Unsupported runner type")

    def graph_command(self, scenario: CompositeScenario):
        # Create directory under output folder to save CompositeScenario config
        graph_json_directory = os.path.join(self.output_dir, "graphs")
        os.makedirs(graph_json_directory, exist_ok=True)

        # Create JSON for krknctl graph runner
        scenario_json = self.__expand_composite_json(scenario)
        json_file = tempfile.mktemp(suffix=".json", dir=graph_json_directory)
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(scenario_json, f, ensure_ascii=False, indent=4)
        logger.info("Created scenario json in path: %s", json_file)

        # Run Json graph
        command = KRKNCTL_GRAPH_RUN_TEMPLATE.format(
            path=json_file, kubeconfig=self.config.kubeconfig_file_path
        )
        return command

    def __expand_composite_json(self, scenario: CompositeScenario, root=0):
        result = {}
        scenario_a = scenario.scenario_a
        scenario_b = scenario.scenario_b

        key_root = str(root)
        key_a = str(root + 1)
        key_b = str(root + 2)

        # Create a dummy scenario which will be the root for scenario A and B.
        if scenario.dependency == CompositeDependency.NONE:
            result[key_root] = self.__generate_scenario_json(
                ScenarioFactory.create_dummy_scenario()
            )

        if isinstance(scenario_a, CompositeScenario):
            result.update(self.__expand_composite_json(scenario_a, root + 3))
        elif isinstance(scenario_a, Scenario):
            key = key_b if scenario.dependency == CompositeDependency.A_ON_B else None
            if scenario.dependency == CompositeDependency.NONE:
                key = key_root
            result[key_a] = self.__generate_scenario_json(
                scenario_a,
                depends_on=key,
            )

        if isinstance(scenario_b, CompositeScenario):
            result.update(self.__expand_composite_json(scenario_b, root + 4))
        elif isinstance(scenario_b, Scenario):
            key = key_a if scenario.dependency == CompositeDependency.B_ON_A else None
            if scenario.dependency == CompositeDependency.NONE:
                key = key_root
            result[key_b] = self.__generate_scenario_json(
                scenario_b,
                depends_on=key,
            )

        return result

    def __generate_scenario_json(self, scenario: Scenario, depends_on: str = None):
        # generate a json based on https://krkn-chaos.dev/docs/krknctl/randomized-chaos-testing/#example
        env = {param.name: str(param.get_value()) for param in scenario.parameters}
        result = {
            "image": f"containers.krkn-chaos.dev/krkn-chaos/krkn-hub:{scenario.name}",
            "name": scenario.name,
            "env": env,
        }
        if depends_on is not None:
            result["depends_on"] = depends_on
        return result

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
        """Calculate fitness score for scenario run"""
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
        """Takes difference between fitness function at start/end intervals of test.
        Helpful to measure values for counter based metric like restarts.
        """
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
        """
        Measure fitness function for the range of test.
        Helpful to measure value over period of time like max cpu usage, max memory usage over time, etc.

        config.fitness_function.query can specify a dynamic "$range$" parameter that will be replaced
        when calling below function.
        """
        logger.info("Calculating Range Fitness")

        query = self.config.fitness_function.query
        # Calculate number of minutes between test run

        if "$range$" in query:
            time_dt_mins = int((end - start).total_seconds() / 60)
            if time_dt_mins == 0:
                time_dt_mins = 1
            query = query.replace("$range$", f"{time_dt_mins}m")
        else:
            logger.warning(
                "You are missing $range$ in config.fitness_function.query to specify dynamic range. Fitness function will use specified range"
            )

        result = self.prom_client.process_prom_query_in_range(
            query,
            start_time=start,
            end_time=end,
            granularity=100,
        )[0]["values"][-1][1]

        return float(result)
