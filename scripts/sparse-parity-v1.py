#!/usr/bin/env python
# coding: utf-8
"""
This script trains MLPs on multiple sparse parity problems at once.

Comments
    - infinite data
"""

from collections import defaultdict
from itertools import islice, product
import random
import time
from pathlib import Path

import numpy as np
import scipy.stats
from tqdm.auto import tqdm

import torch
import torch.nn as nn

from sacred import Experiment
from sacred.utils import apply_backspaces_and_linefeeds
ex = Experiment("sparse-parity-v1")
ex.captured_out_filter = apply_backspaces_and_linefeeds


def get_batch(n_tasks, n, Ss, codes, sizes, device='cpu', dtype=torch.float64):
    """Creates batch. 

    Parameters
    ----------
    n_tasks : int
        Number of tasks.
    n : int
        Bit string length for sparse parity problem.
    Ss : list of lists of ints
        Subsets of [1, ... n] to compute sparse parities on.
    codes : list of int
        The subtask indices which the batch will consist of
    sizes : list of int
        Number of samples for each subtask
    device : str
        Device to put batch on.
    dtype : torch.dtype
        Data type to use for input x. Output y is torch.int64.

    Returns
    -------
    x : torch.Tensor
        inputs
    y : torch.Tensor
        labels
    """
    batch_x = torch.zeros((sum(sizes), n_tasks+n), device=device)
    batch_y = torch.zeros((sum(sizes),), dtype=torch.int64, device=device)
    start_i = 0
    for (S, size, code) in zip(Ss, sizes, codes):
        if size > 0:
            x = torch.randint(low=0, high=2, size=(size, n), device=device)
            y = torch.sum(x[:, S], dim=1) % 2
            x_task_code = torch.zeros((size, n_tasks), device=device)
            x_task_code[:, code] = 1
            x = torch.cat([x_task_code, x], dim=1)
            x = x.to(torch.float64)
            batch_x[start_i:start_i+size, :] = x
            batch_y[start_i:start_i+size] = y
            start_i += size
    return batch_x.to(dtype), batch_y
    

# --------------------------
#    ,-------------.
#   (_\  CONFIG     \
#      |    OF      |
#      |    THE     |
#     _| EXPERIMENT |
#    (_/_____(*)___/
#             \\
#              ))
#              ^
# --------------------------
@ex.config
def cfg():
    n_tasks = 100
    n = 50
    k = 3
    alpha = 1.5

    width = 100
    depth = 2
    activation = 'ReLU'
    
    steps = 25000
    batch_size = 10000
    lr = 1e-3
    test_points = 30000
    test_points_per_task = 1000
    
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    dtype = torch.float64

    log_freq = steps // 1000
    verbose=False

# --------------------------
#  |-|    *
#  |-|   _    *  __
#  |-|   |  *    |/'   SEND
#  |-|   |~*~~~o~|     IT!
#  |-|   |  O o *|
# /___\  |o___O__|
# --------------------------
@ex.automain
def run(n_tasks,
        n,
        k,
        alpha,
        width,
        depth,
        activation,
        test_points,
        test_points_per_task,
        steps,
        batch_size,
        lr,
        device,
        dtype,
        log_freq,
        verbose,
        seed,
        _log):

    torch.set_default_dtype(dtype)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)

    if activation == 'ReLU':
        activation_fn = nn.ReLU
    elif activation == 'Tanh':
        activation_fn = nn.Tanh
    elif activation == 'Sigmoid':
        activation_fn = nn.Sigmoid
    else:
        assert False, f"Unrecognized activation function identifier: {activation}"

    # create model
    layers = []
    for i in range(depth):
        if i == 0:
            layers.append(nn.Linear(n_tasks + n, width))
            layers.append(activation_fn())
        elif i == depth - 1:
            layers.append(nn.Linear(width, 2))
        else:
            layers.append(nn.Linear(width, width))
            layers.append(activation_fn())
    mlp = nn.Sequential(*layers).to(device)
    _log.debug("Created model.")
    _log.debug(f"Model has {sum(t.numel() for t in mlp.parameters())} parameters") 
    
    ex.info['P'] = sum(t.numel() for t in mlp.parameters())
    ex.info['D'] = steps * batch_size

    Ss = [random.sample(range(n), k) for _ in range(n_tasks)]
    ex.info['Ss'] = Ss
    
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(mlp.parameters(), lr=lr)
    ex.info['log_steps'] = list()
    ex.info['accuracies'] = list()
    ex.info['losses'] = list()
    ex.info['losses_subtasks'] = defaultdict(list)
    ex.info['accuracies_subtasks'] = defaultdict(list)
    for step in tqdm(range(steps), disable=not verbose):
        if step % log_freq == 0:
            with torch.no_grad():
                samples = scipy.stats.zipfian.rvs(alpha, n_tasks, size=test_points)
                hist = hist = defaultdict(int)
                for s in samples:
                    hist[s] += 1
                codes = list(hist.keys())
                sizes = [hist[c] for c in codes]
                batch_Ss = [Ss[c] for c in codes]
                x_i, y_i = get_batch(n_tasks=n_tasks, n=n, Ss=batch_Ss, codes=codes, sizes=sizes, device=device, dtype=dtype)
                y_i_pred = mlp(x_i)
                labels_i_pred = torch.argmax(y_i_pred, dim=1)
                ex.info['accuracies'].append(torch.sum(labels_i_pred == y_i).item() / test_points) 
                ex.info['losses'].append(loss.item())
                for i in range(n_tasks):
                    x_i, y_i = get_batch(n_tasks=n_tasks, n=n, Ss=[Ss[i]], codes=[i], sizes=[test_points_per_task], device=device)
                    y_i_pred = mlp(x_i)
                    ex.info['losses_subtasks'][i].append(loss_fn(y_i_pred, y_i).item())
                    labels_i_pred = torch.argmax(y_i_pred, dim=1)
                    ex.info['accuracies_subtasks'][i].append(torch.sum(labels_i_pred == y_i).item() / test_points_per_task)

        optimizer.zero_grad()
        samples = scipy.stats.zipfian.rvs(alpha, n_tasks, size=batch_size)
        hist = hist = defaultdict(int)
        for s in samples:
            hist[s] += 1
        codes = list(hist.keys())
        sizes = [hist[c] for c in codes]
        batch_Ss = [Ss[c] for c in codes]
        x, y_target = get_batch(n_tasks=n_tasks, n=n, Ss=batch_Ss, codes=codes, sizes=sizes, device=device, dtype=dtype)
        y_pred = mlp(x)
        loss = loss_fn(y_pred, y_target)
        loss.backward()
        optimizer.step()

