import datetime
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
            cmd=command,
            log=log,
            returncode=returncode,
            start_time=start_time,
            end_time=end_time
        )
