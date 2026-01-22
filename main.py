import sys
import os
import json
import requests
import asyncio

from openai import OpenAI
from parallel import Parallel


MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

parallel_client = Parallel(
    api_key=os.environ["PARALLEL_API_KEY"],
    default_headers={"parallel-beta": "search-extract-2025-10-10"}
    )
client = OpenAI()
PARALLEL_BETAS = ["search-extract-2025-10-10"]


def init_state(prompt: str):
    return {
        "prompt": prompt,
        "plan": [],
        "tasks": [],
        "search_log": [],     # list of {agent, objective, urls}
        "evidence": [],       # list of {agent, url, excerpts}
    }



async def run_controller(state):
    planner_agent(state)
    await run_exploration(state)
    summarizer_agent(state)
    markdown_agent(state)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your research prompt"')
        raise SystemExit(1)

    prompt = sys.argv[1].strip()
    state = init_state(prompt)

    # use cached state - remove this
    # with open('state.json', 'r') as file:
    #     data_dict = json.load(file)
    # state = data_dict

    asyncio.run(run_controller(state))

    ### cache state remove this
    # file_path = "state.json"
    # with open(file_path, "w") as json_file:
    #     json.dump(state, json_file, indent=4)

    print("Success")


# python3 main.py "tell me about the societal impact of AI"