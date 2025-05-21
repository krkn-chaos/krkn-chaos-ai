from chaos_ai.models.base_scenario import ScenarioFactory
from chaos_ai.models.config import ConfigFile
from chaos_ai.utils.logger import get_module_logger

logger = get_module_logger(__name__)

DEBUG_MODE = True


class GeneticAlgorithm:
    def __init__(self, config: ConfigFile):
        self.config = config
        self.population = []

    def simulate(self):
        self.create_population()

    def create_population(self):
        '''Generate random population for algorithm'''
        logger.info("Creating random population")
        logger.info("Population Size: %d", self.config.population_size)

        while len(self.population) != self.config.population_size:
            scenario = ScenarioFactory.generate_random_scenario(self.config)
            if scenario:
                self.population.append(scenario)

        if DEBUG_MODE:
            logger.info("\n| Population |")
            logger.info("--------------------------------------------------------")
            for scenario in self.population:
                logger.info("%s, ", scenario)
            logger.info("--------------------------------------------------------\n")
