from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import numpy as np
import torch
from torch import tensor
from sklearn.metrics import roc_curve, auc, accuracy_score, confusion_matrix, classification_report

from .models import RatioModel
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def evaluate_ratio_model(
    model,
    xs=None,
    run_on_gpu=False,#True,
    double_precision=False,
    return_grad_x=False,
):
    # CPU or GPU?
    run_on_gpu = run_on_gpu and torch.cuda.is_available()
    device = torch.device("cuda" if run_on_gpu else "cpu")
    dtype = torch.double if double_precision else torch.float

    # Prepare data
    n_xs = len(xs)
    xs = torch.stack([tensor(i) for i in xs])

    model = model.to(device, dtype)
    xs = xs.to(device, dtype)
    with torch.no_grad():
        model.eval()

        r_hat, s_hat  = model(xs)
        s_hat = torch.sigmoid(s_hat)
        # Copy back tensors to CPU
        if run_on_gpu:
            r_hat = r_hat.cpu()
            s_hat = s_hat.cpu()

        # Get data and return
        r_hat = r_hat.detach().numpy().flatten()
        s_hat = s_hat.detach().numpy().flatten()
    return r_hat, s_hat

def evaluate_performance_model(
    model,
    xs,
    ys,
    run_on_gpu=True,
    double_precision=False,
    return_grad_x=False,
):
    # CPU or GPU?
    run_on_gpu = run_on_gpu and torch.cuda.is_available()
    device = torch.device("cuda" if run_on_gpu else "cpu")
    dtype = torch.double if double_precision else torch.float

    # Prepare data
    n_xs = len(xs)
    xs = torch.stack([tensor(i) for i in xs])

    model = model.to(device, dtype)
    xs = xs.to(device, dtype)

    with torch.no_grad():
        model.eval()

        _, logit  = model(xs)
        probs = torch.sigmoid(logit)
        y_pred = torch.round(probs)
        print("confusion matrix ",confusion_matrix(ys, y_pred))
        print(classification_report(ys, y_pred))
        fpr, tpr, auc_thresholds = roc_curve(ys, y_pred)

def plot_roc_curve(fpr, tpr, label=None):
    plt.figure(figsize=(8,8))
    plt.title('ROC Curve')
    plt.plot(fpr, tpr, linewidth=2, label=label)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.axis([-0.005, 1, 0, 1.005])
    plt.xticks(np.arange(0,1, 0.05), rotation=90)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.legend(loc='best')
