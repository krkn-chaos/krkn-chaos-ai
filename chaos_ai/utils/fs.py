import os
import yaml
import shlex
import subprocess

from chaos_ai.models.config import ConfigFile
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)


def read_config_from_file(file_path: str) -> ConfigFile:
    """Read config file from local"""
    with open(file_path, "r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    return ConfigFile(**config)


def run_shell(command, do_not_log=False):
    '''
    Run shell command and get logs and statuscode in output.
    '''
    logger.debug("Running command: %s", command)
    logs = ""
    command = shlex.split(command)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in process.stdout:
        if not do_not_log:
            logger.debug("%s", line.rstrip())
        logs += line
    process.wait()
    logger.debug("Run Status: %d", process.returncode)
    return logs, process.returncode


def env_is_truthy(var: str):
    '''
    Checks whether a environment variable is set to truthy value.
    '''
    value = os.getenv(var, 'false')
    value = value.lower().strip()
    return value in ['yes', 'y', 'true', '1']
