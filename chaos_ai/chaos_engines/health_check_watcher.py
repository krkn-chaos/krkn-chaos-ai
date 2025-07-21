'''
This module is used to run health checks for the application URLs and keep track of the results.

Working Details:
1. Asynchronous health check for each URL.
2. Keep track of the results in a list.
3. Once there is signal from main thread that the test is complete, or in case the api status check fails, then the watcher stops.
4. Return the results to the main thread by seperate method.
'''

from collections import defaultdict
import threading
import time
import requests
from typing import List, Dict

from chaos_ai.utils.logger import get_module_logger
from chaos_ai.models.config import HealthCheckConfig, HealthCheckResult

logger = get_module_logger(__name__)

class HealthCheckWatcher:
    def __init__(self, config: List[HealthCheckConfig]):
        self.config = config
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []
        # Each thread stores results in its own list - ZERO contention!
        self._thread_results = {}

    def run(self):
        # Start a thread for each health check
        logger.info(f"Starting health check watcher for {len(self.config)} health checks")
        for health_check in self.config:
            t = threading.Thread(target=self.run_health_check, args=(health_check,))
            t.start()
            self._threads.append(t)

    def run_health_check(self, health_check: HealthCheckConfig):
        # Each thread gets its own private results list
        thread_id = threading.current_thread().ident
        thread_results = []
        self._thread_results[thread_id] = (health_check.url, thread_results)
        
        # Simple polling loop, stops when stop() is called
        while not self._stop_event.is_set():
            try:
                resp = requests.get(health_check.url, timeout=health_check.timeout)
                status = resp.status_code
                success = (status == 200)
                error = None
            except Exception as e:
                status = -1
                success = False
                resp = None
                error = str(e)

            result = HealthCheckResult(
                status_code=status,
                success=success,
                error=error,
                response_time=resp.elapsed.total_seconds() if resp is not None else -1
            )
            
            # Store in thread-private list - NO LOCKS, NO CONTENTION!
            thread_results.append(result)

            if not success:
                self._stop_event.set()
                break

            time.sleep(health_check.interval)

    def stop(self):
        logger.info(f"Stopping health check watcher")
        self._stop_event.set()
        for t in self._threads:
            t.join()

    def get_results(self) -> Dict[str, List[HealthCheckResult]]:
        """Aggregate results from all threads - called after threads complete"""
        results = defaultdict(list)
        
        # Each thread has its own URL and results list
        for url, thread_results in self._thread_results.values():
            results[url].extend(thread_results)
                
        return dict(results)
