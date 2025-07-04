import os
import click
from pydantic import ValidationError
from chaos_ai.utils.fs import read_config_from_file
from chaos_ai.utils.logger import get_module_logger

from chaos_ai.algorithm.genetic import GeneticAlgorithm


logger = get_module_logger(__name__)


@click.group()
def main():
    pass


@main.command()
@click.option('--config', '-c', help='Path to chaos ai config file.')
@click.option('--output', '-o', help='Directory to save result.')
def run(config: str, output: str = "./"):
    if config == '' or config is None:
        logger.warning("Config file invalid.")
        exit(1)
    if not os.path.exists(config):
        logger.warning("Config file not found.")
        exit(1)

    try:
        logger.debug("Config File: %s", config)
        parsed_config = read_config_from_file(config)
        logger.debug("Successfully parsed config!")
    except ValidationError as err:
        logger.error("Unable to parse config file: %s", err)
        exit(1)

    genetic = GeneticAlgorithm(
        parsed_config,
        output_dir=output
    )
    genetic.simulate()

    genetic.save()
