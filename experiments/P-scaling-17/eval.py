
import random
import time

from itertools import product
import os
import sys

import numpy as np

widths = [int(w) for w in np.power(2, np.linspace(np.log2(10), np.log2(300), 20))]
alphas = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]
seeds = [0, 1, 2]
configs = list(product(widths, alphas, seeds)) # 480

if __name__ == '__main__':

    task_idx = int(sys.argv[1])
    # time.sleep(5 * task_idx)

    width, alpha, seed = configs[task_idx]
    # run a command from the commandline with the os package
    os.system(f"""python /om2/user/ericjm/the-everything-machine/scripts/sparse-parity-v4.py \
                                -F /om/user/ericjm/results/the-everything-machine/P-scaling-17 \
                                run with \
                                alpha={alpha} \
                                offset=0 \
                                D=-1 \
                                batch_size=20000 \
                                width={width} \
                                depth=2 \
                                k=3 \
                                n=100 \
                                steps=100000 \
                                n_tasks=500 \
                                log_freq=500 \
                                test_points=1000000 \
                                test_points_per_task=1000 \
                                seed={seed} \
                                """)


