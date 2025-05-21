import yaml
import shlex
import subprocess
from chaos_ai.models.config import ConfigFile


def read_config_from_file(file_path: str) -> ConfigFile:
    """Read config file from local"""
    with open(file_path, "r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    return ConfigFile(**config)


def run_shell(command):
    '''
    Run shell command and get logs and statuscode in output.
    '''
    logs = ""
    command = shlex.split(command)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in process.stdout:
        logs += line
    process.wait()
    return logs, process.returncode
