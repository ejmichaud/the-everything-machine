
import random
import time

from itertools import product
import os
import sys

import numpy as np

Ds = list(range(1000, 20000, 1000)) # 19

if __name__ == '__main__':

    task_idx = int(sys.argv[1])
    time.sleep(task_idx * 5)    

    D = Ds[task_idx]
    # run a command from the commandline with the os package
    os.system(f"""python /om2/user/ericjm/the-everything-machine/scripts/sparse-parity-v2.py \
                                -F /om/user/ericjm/results/the-everything-machine/onetask-D-scaling-1 \
                                run with \
                                alpha=1.4 \
                                D={D} \
                                batch_size=10000 \
                                width=500 \
                                depth=2 \
                                k=2 \
                                n=200 \
                                n_tasks=1 \
                                steps=20000 \
                                log_freq=50 \
                                test_points=5000 \
                                seed=0
                                """)

