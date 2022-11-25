
import random
import time

from itertools import product
import os
import sys

import numpy as np

Ds = [int(D) for D in np.power(2, np.linspace(np.log2(1000), np.log2(100000), 30))]

if __name__ == '__main__':

    task_idx = int(sys.argv[1])
    time.sleep(task_idx * 5)    

    D = Ds[task_idx]
    # run a command from the commandline with the os package
    os.system(f"""python /om2/user/ericjm/the-everything-machine/scripts/sparse-parity-v2.py \
                                -F /om/user/ericjm/results/the-everything-machine/D-scaling-0 \
                                run with \
                                alpha=1.4 \
                                D={D} \
                                batch_size=15000 \
                                width=1000 \
                                depth=2 \
                                k=3 \
                                n=100 \
                                n_tasks=500 \
                                steps=200000 \
                                log_freq=50 \
                                test_points=60000 \
                                seed=0
                                """)
