from __future__ import annotations

from collections import deque
import sys
from dotenv import load_dotenv

from models.execution_jobs import ExecutionJob
from utils.util import get_env

load_dotenv()
PROFILES_CREDTS = get_env("PROFILES_CREDTS")

dq = deque()

import logging

if __name__ == "__main__":
    args = list(sys.argv)[1:]
    # with open("/etc/proxychains.conf", "r") as f:
    #         print(f.read())
    # args = ["instagram", "hamza_kar132", "r62DUra9Q33nXk8A"]
    # args = ["facebook", "marouanezkaoui@gmail.com", "S89z5yLkW@mjyMpvT"]

    logger = logging.getLogger("root")
    logger.setLevel(level=logging.DEBUG)

    ExecutionJob(profiles_path=PROFILES_CREDTS, dq=dq).run_jobs(args)
