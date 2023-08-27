# Copyright The Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional

import torch
from torch import Tensor

from torchmetrics.utilities.checks import _check_same_shape


def calculate_contingency_matrix(
    preds: Tensor, target: Tensor, eps: Optional[float] = None, sparse: bool = False
) -> Tensor:
    """Calculate contingency matrix.

    Args:
        preds: predicted labels
        target: ground truth labels
        eps: value added to contingency matrix
        sparse: If True, returns contingency matrix as a sparse matrix. Else, return as dense matrix.
            `eps` must be `None` if `sparse` is `True`.

    Returns:
        contingency: contingency matrix of shape (n_classes_target, n_classes_preds)

    Example:
        >>> import torch
        >>> from torchmetrics.functional.clustering.utils import calculate_contingency_matrix
        >>> preds = torch.tensor([2, 1, 0, 1, 0])
        >>> target = torch.tensor([0, 2, 1, 1, 0])
        >>> calculate_contingency_matrix(preds, target, eps=1e-16)
        tensor([[1.0000e+00, 1.0000e-16, 1.0000e+00],
                [1.0000e+00, 1.0000e+00, 1.0000e-16],
                [1.0000e-16, 1.0000e+00, 1.0000e-16]])

    """
    if eps is not None and sparse is True:
        raise ValueError("Cannot specify `eps` and return sparse tensor.")
    if preds.ndim != 1 or target.ndim != 1:
        raise ValueError(f"Expected 1d `preds` and `target` but got {preds.ndim} and {target.dim}.")

    preds_classes, preds_idx = torch.unique(preds, return_inverse=True)
    target_classes, target_idx = torch.unique(target, return_inverse=True)

    n_classes_preds = preds_classes.size(0)
    n_classes_target = target_classes.size(0)

    contingency = torch.sparse_coo_tensor(
        torch.stack(
            (
                target_idx,
                preds_idx,
            )
        ),
        torch.ones(target_idx.shape[0], dtype=preds_idx.dtype, device=preds_idx.device),
        (
            n_classes_target,
            n_classes_preds,
        ),
    )

    if not sparse:
        contingency = contingency.to_dense()
        if eps:
            contingency = contingency + eps

    return contingency


def check_cluster_labels(preds: Tensor, target: Tensor) -> None:
    """Check shape of input tensors and if they are real, discrete tensors.

    Args:
        preds: predicted labels
        target: ground truth labels

    """
    _check_same_shape(preds, target)
    if preds.ndim != 1:
        raise ValueError(f"Expected arguments to be 1d tensors but got {preds.ndim} and {target.ndim}")
    if (
        torch.is_floating_point(preds)
        or torch.is_complex(preds)
        or torch.is_floating_point(target)
        or torch.is_complex(target)
    ):
        raise ValueError(
            f"Expected real, discrete values but received {preds.dtype} for"
            f"predictions and {target.dtype} for target labels instead."
        )