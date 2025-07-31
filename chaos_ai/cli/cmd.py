import logging
import os
import click
from pydantic import ValidationError
from chaos_ai.utils.fs import read_config_from_file
from chaos_ai.utils.logger import get_module_logger, verbosity_to_level
from chaos_ai.models.app import AppContext, KrknRunnerType

from chaos_ai.algorithm.genetic import GeneticAlgorithm


@click.group()
def main():
    pass

# TODO: Verbose mode
@main.command()
@click.option('--config', '-c', help='Path to chaos AI config file.')
@click.option('--output', '-o', help='Directory to save results.')
@click.option('--format', '-f', help='Format of the output file.',
    type=click.Choice(['json', 'yaml'], case_sensitive=False),
    default='yaml'
)
@click.option('--runner-type', '-r', 
              type=click.Choice(['krknctl', 'krknhub'], case_sensitive=False),
              help='Type of chaos engine to use.', default=None)
@click.option(
    '--param', '-p',
    multiple=True,
    help='Additional parameters for config file in key=value format.',
    default=[]
)
@click.option('-v', '--verbose', count=True, help='Increase verbosity of output.')
@click.pass_context
def run(ctx,
    config: str,
    output: str = "./",
    format: str = 'yaml',
    runner_type: str = None,
    param: list[str] = None,
    verbose: int = 0       # Default to INFO level
):
    ctx.obj = AppContext(verbose=verbosity_to_level(verbose))

    logger = get_module_logger(__name__)

    if config == '' or config is None:
        logger.warning("Config file invalid.")
        exit(1)
    if not os.path.exists(config):
        logger.warning("Config file not found.")
        exit(1)

    try:
        logger.debug("Config File: %s", config)
        parsed_config = read_config_from_file(config, param)
        logger.debug("Successfully parsed config!")
    except ValidationError as err:
        logger.error("Unable to parse config file: %s", err)
        exit(1)

    # Convert user-friendly string to enum if provided
    enum_runner_type = None
    if runner_type:
        if runner_type.lower() == 'krknctl':
            enum_runner_type = KrknRunnerType.CLI_RUNNER
        elif runner_type.lower() == 'krknhub':
            enum_runner_type = KrknRunnerType.HUB_RUNNER

    genetic = GeneticAlgorithm(
        parsed_config,
        output_dir=output,
        format=format,
        runner_type=enum_runner_type
    )
    genetic.simulate()

    genetic.save()
