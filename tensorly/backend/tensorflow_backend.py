try:
    import tensorflow as tf
    import tensorflow.math as tfm
    import tensorflow.experimental.numpy as tnp
except ImportError as error:
    message = (
        "Impossible to import TensorFlow.\n"
        "To use TensorLy with the TensorFlow backend, "
        "you must first install TensorFlow!"
    )
    raise ImportError(message) from error

import numpy as np

from . import Backend


class TensorflowBackend(Backend, backend_name="tensorflow"):
    @staticmethod
    def context(tensor):
        return {"dtype": tensor.dtype}

    @staticmethod
    def tensor(data, dtype=np.float64, device=None, device_id=None):
        if isinstance(data, tf.Tensor) or isinstance(data, tf.Variable):
            return tf.cast(data, dtype=dtype)

        out = tf.Variable(data, dtype=dtype)
        return out.gpu(device_id) if device == "gpu" else out

    @staticmethod
    def is_tensor(tensor):
        return isinstance(tensor, tf.Tensor) or isinstance(tensor, tf.Variable)

    @staticmethod
    def to_numpy(tensor):
        if isinstance(tensor, np.ndarray):
            return tensor
        elif isinstance(tensor, tf.Tensor):
            return tensor.numpy()
        elif isinstance(tensor, tf.Variable):
            return tf.convert_to_tensor(tensor).numpy()
        else:
            return tensor

    @staticmethod
    def shape(tensor):
        return tuple(tensor.shape.as_list())

    @staticmethod
    def norm(tensor, order=2, axis=None):
        if order == "inf":
            order = np.inf
        return tf.norm(tensor=tensor, ord=order, axis=axis)

    @staticmethod
    def solve(lhs, rhs):
        squeeze = False
        if rhs.ndim == 1:
            squeeze = [-1]
            rhs = tf.reshape(rhs, (-1, 1))
        res = tf.linalg.solve(lhs, rhs)
        if squeeze:
            res = tf.squeeze(res, squeeze)
        return res

    @staticmethod
    def clip(tensor, a_min=None, a_max=None):
        return tnp.clip(tensor, a_min, a_max)

    @staticmethod
    def lstsq(a, b):
        n = a.shape[1]
        if tf.rank(b) == 1:
            x = tf.squeeze(tf.linalg.lstsq(a, tf.expand_dims(b, -1), fast=False), -1)
        else:
            x = tf.linalg.lstsq(a, b, fast=False)
        residuals = tf.norm(tf.tensordot(a, x, 1) - b, axis=0) ** 2
        return x, residuals if tf.linalg.matrix_rank(a) == n else tf.constant([])

    def svd(self, matrix, full_matrices):
        """Correct for the atypical return order of tf.linalg.svd."""
        S, U, V = tf.linalg.svd(matrix, full_matrices=full_matrices)
        return U, S, tf.transpose(a=V)

    def index_update(self, tensor, indices, values):
        if not isinstance(tensor, tf.Variable):
            tensor = tf.Variable(tensor)
            to_tensor = True
        else:
            to_tensor = False

        if isinstance(values, int):
            values = tf.constant(
                np.ones(self.shape(tensor[indices])) * values, **self.context(tensor)
            )

        tensor = tensor[indices].assign(values)

        if to_tensor:
            return tf.convert_to_tensor(tensor)
        else:
            return tensor


# Register numpy functions
for name in ["nan"]:
    TensorflowBackend.register_method(name, getattr(np, name))


# Register linalg functions
for name in ["diag", "qr", "eigh", "trace"]:
    TensorflowBackend.register_method(name, getattr(tf.linalg, name))


# Register tfm functions
for name in [
    "exp",
    "log",
    "digamma",
    "atanh",
    "acosh",
    "asinh",
    "tanh",
    "cosh",
    "sinh",
    "atan",
    "acos",
    "asin",
    "sin",
    "cos",
    "tan",
]:
    TensorflowBackend.register_method(name, getattr(tfm, name))


# Register tnp functions
for name in [
    "log2",
    "concatenate",
    "flip",
    "dot",
    "matmul",
    "cumsum",
    "argmin",
    "argmax",
    "any",
    "e",
    "inf",
    "pi",
    "conj",
    "arctanh",
    "arccosh",
    "arcsinh",
    "arctan",
    "arccos",
    "arcsin",
    "tensordot",
    "sign",
    "stack",
    "copy",
    "min",
    "max",
    "mean",
    "sum",
    "prod",
    "all",
    "eye",
    "where",
    "ones",
    "zeros",
    "abs",
    "sqrt",
    "zeros_like",
    "int32",
    "int64",
    "float32",
    "float64",
    "complex64",
    "complex128",
    "moveaxis",
    "ndim",
    "arange",
    "sort",
    "argsort",
    "flip",
    "einsum",
    "stack",
    "reshape",
    "transpose",
    "count_nonzero",
]:
    TensorflowBackend.register_method(name, getattr(tnp, name))
