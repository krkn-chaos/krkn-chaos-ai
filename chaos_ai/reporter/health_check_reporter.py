import os
import pandas as pd
from typing import List

from chaos_ai.models.app import CommandRunResult


class HealthCheckReporter:
    def __init__(self, output_dir: str):
        self.output_dir = os.path.join(output_dir, "reports")
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_and_save_report(self, fitness_results: List[CommandRunResult]):
        results = self.generate_report_data(fitness_results)
        results.to_csv(os.path.join(self.output_dir, "health_check_report.csv"), index=False)

    def generate_report_data(self, fitness_results: List[CommandRunResult]):
        results = []

        for fitness_result in fitness_results:
            health_check_results = fitness_result.health_check_results.values()
            scenario_id = fitness_result.scenario_id
            
            for component_results in health_check_results:
                if len(component_results) == 0:
                    break
                component_name = component_results[0].name
                min_response_time = min([result.response_time for result in component_results])
                max_response_time = max([result.response_time for result in component_results])
                average_response_time = sum([result.response_time for result in component_results]) / len(component_results)
                success_count = sum([result.success for result in component_results])
                failure_count = len(component_results) - success_count

                results.append({
                    "scenario_id": scenario_id,
                    "component_name": component_name,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "average_response_time": average_response_time,
                    "success_count": success_count,
                    "failure_count": failure_count,
                })

        return pd.DataFrame(results)

