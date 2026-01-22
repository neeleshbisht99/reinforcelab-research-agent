import os
from parallel import Parallel

class ParallelClient:
    def __init__(self, beta_version: str):
        self.betas = [beta_version]
        self.client = Parallel(
            api_key=os.environ["PARALLEL_API_KEY"],
            default_headers={"parallel-beta": beta_version},
        )

    def search(self, objective: str, *, search_queries=None, max_results=10, max_chars=200):
        resp = self.client.beta.search(
            objective=objective,
            search_queries=search_queries or [],
            max_results=max_results,
            excerpts={"max_chars_per_result": max_chars},
        )
        return resp.results

    def extract(self, urls, objective: str, *, max_chars=1000):
        resp = self.client.beta.extract(
            betas=self.betas,
            urls=urls,
            objective=objective,
            excerpts={"max_chars_per_result": max_chars},
            full_content=False,
        )
        return resp.results