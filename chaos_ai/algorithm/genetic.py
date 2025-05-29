import os
import copy
import json
import random
from typing import List

from chaos_ai.models.app import CommandRunResult
from chaos_ai.models.base_scenario import Scenario, ScenarioFactory
from chaos_ai.models.config import ConfigFile
from chaos_ai.utils.logger import get_module_logger
from chaos_ai.chaos_engines.krkn_hub_runner import KrknHubRunner

logger = get_module_logger(__name__)

DEBUG_MODE = True


class GeneticAlgorithm:
    def __init__(self, config: ConfigFile):
        self.krkn_client = KrknHubRunner(config)
        self.config = config
        self.population = []

        self.seen_population = {}  # Map between scenario and its result
        self.best_of_generation = []

    def simulate(self):
        self.create_population()

        for i in range(self.config.generations):
            if len(self.population) == 0:
                logger.warning("No more population found, stopping generations.")
                break

            logger.info("| Population |")
            logger.info("--------------------------------------------------------")
            for scenario in self.population:
                logger.info("%s, ", scenario)
            logger.info("--------------------------------------------------------")

            logger.info("| Generation %d |", i + 1)
            logger.info("--------------------------------------------------------")

            # Evaluate fitness of the current population
            fitness_scores = [
                self.calculate_fitness(member, i) for member in self.population
            ]
            # Find the best individual in the current generation
            # Note: If there is no best solution, it will still consider based on sorting order
            fitness_scores = sorted(
                fitness_scores, key=lambda x: x.fitness_score, reverse=True
            )
            self.best_of_generation.append(fitness_scores[0])
            logger.info("Best Fitness: %f", fitness_scores[0].fitness_score)

            # We don't want to add a same parent back to population since its already been included
            for fitness_result in fitness_scores:
                self.seen_population[fitness_result.scenario] = fitness_result

            # Repopulate off-springs
            self.population = []
            for _ in range(self.config.population_size // 2):
                parent1, parent2 = self.select_parents(fitness_scores)
                child1, child2 = self.crossover(
                    copy.deepcopy(parent1), copy.deepcopy(parent2)
                )
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)

                self.population.append(child1)
                self.population.append(child2)

    def create_population(self):
        """Generate random population for algorithm"""
        logger.info("Creating random population")
        logger.info("Population Size: %d", self.config.population_size)

        already_seen = set()

        while len(self.population) != self.config.population_size:
            scenario = ScenarioFactory.generate_random_scenario(self.config)
            # Mutate to generate initial randomness among same tests
            scenario = self.mutate(scenario)
            if scenario and scenario not in already_seen:
                self.population.append(scenario)
                already_seen.add(scenario)

    def calculate_fitness(self, scenario: Scenario, generation_id: int):
        # If scenario has already been run, do not run it again.
        # we will rely on mutation for the same parents to produce newer samples
        if scenario in self.seen_population:
            logger.info("Scenario %s already evaluated, skipping fitness calculation.", scenario)
            scenario = copy.deepcopy(self.seen_population[scenario])
            scenario.generation_id = generation_id
            return scenario
        return self.krkn_client.run(scenario, generation_id)

    def mutate(self, scenario: Scenario):
        for param in scenario.parameters:
            if random.random() < 0.6:
                param.mutate()
        return scenario

    def select_parents(self, fitness_scores: List[CommandRunResult]):
        """
        Selects two parents using Roulette Wheel Selection (proportionate selection).
        Higher fitness means higher chance of being selected.
        """
        total_fitness = sum([x.fitness_score for x in fitness_scores])

        scenarios = [x.scenario for x in fitness_scores]

        if total_fitness == 0:  # Handle case where all fitness scores are zero
            return random.choice(scenarios), random.choice(scenarios)

        # Normalize fitness scores to get probabilities
        probabilities = [x.fitness_score / total_fitness for x in fitness_scores]

        # Select parents based on probabilities
        parent1 = random.choices(scenarios, weights=probabilities, k=1)[0]
        parent2 = random.choices(scenarios, weights=probabilities, k=1)[0]
        return parent1, parent2

    def crossover(self, scenario_a: Scenario, scenario_b: Scenario):
        common_params = set([x.name for x in scenario_a.parameters]) & set(
            [x.name for x in scenario_b.parameters]
        )

        def find_param_index(scenario: Scenario, param_name):
            for i, param in enumerate(scenario.parameters):
                if param_name == param.name:
                    return i

        if len(common_params) == 0:
            # no common parameter, currenty we return parents as is and hope for mutation
            # adopt some different strategy
            return scenario_a, scenario_b
        else:
            # if there are common params, lets switch values between them
            for param in common_params:
                if random.random() < 0.8:
                    # find index of param in list
                    a_index = find_param_index(scenario_a, param)
                    b_index = find_param_index(scenario_b, param)

                    # swap param values
                    valueA = scenario_a.parameters[a_index].value
                    valueB = scenario_b.parameters[b_index].value

                    scenario_a.parameters[a_index].value = valueB
                    scenario_b.parameters[b_index].value = valueA

            return scenario_a, scenario_b

    def save(self, output_dir: str):
        logger.info("Saving results to generations.json")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        with open(
            os.path.join(output_dir, "generations.json"),
            "w",
            encoding="utf-8"
        ) as f:
            # Store data per generation
            data = {}

            for job_id, fitness_result in enumerate(self.seen_population.values()):
                scenario_result = fitness_result.model_dump()
                generation_id = scenario_result['generation_id']
                scenario_result['job_id'] = job_id

                # Store log in a log file and update log location
                scenario_result['log'] = self.save_log_file(
                    str(job_id),
                    scenario_result['log'],
                    output_dir
                )
                # Convert timestamps to ISO string
                scenario_result['start_time'] = (scenario_result['start_time']).isoformat()
                scenario_result['end_time'] = (scenario_result['end_time']).isoformat()

                if generation_id in data:
                    data[generation_id].append(scenario_result)
                else:
                    data[generation_id] = [scenario_result]

            json.dump(data, f, indent=4)

    def save_log_file(self, job_id: str, log_data: str, output_dir: str):
        dir_path = os.path.join(output_dir, 'logs')
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        # Store log file in output directory under a "logs" folder.
        log_save_path = os.path.join(dir_path, job_id + ".log")
        with open(log_save_path, 'w', encoding='utf-8') as f:
            f.write(log_data)
        return log_save_path
