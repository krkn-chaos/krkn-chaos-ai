import os
import click
from chaos_ai.utils.fs import read_config_from_file
from chaos_ai.utils.logger import get_module_logger

from chaos_ai.algorithm.genetic import GeneticAlgorithm
from chaos_ai.chaos_engines.krkn_hub_runner import KrknHubRunner

logger = get_module_logger(__name__)


@click.group()
def main():
    pass


@main.command()
@click.option('--config', '-c', help='Path to chaos ai config file.')
def run(config: str):
    if config == '' or config is None:
        logger.warning("Config file invalid.")
        exit(1)
    if not os.path.exists(config):
        logger.warning("Config file not found.")
        exit(1)

    logger.debug("Config File: %s", config)

    parsed_config = read_config_from_file(config)
    logger.debug("Successfully parsed config!")

    genetic = GeneticAlgorithm(parsed_config)
    genetic.simulate()
