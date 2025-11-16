"""
Apply ForwardRef._evaluate patch for Python 3.12 to avoid recursive_guard errors with pydantic v1.
"""
import inspect
import typing


def apply_forwardref_patch():
    _fr_eval = typing.ForwardRef._evaluate
    _fr_sig = inspect.signature(_fr_eval)
    if "recursive_guard" in _fr_sig.parameters:
        def _patched_forward_ref(self, globalns, localns, *args, **kwargs):
            kwargs.setdefault("recursive_guard", set())
            return _fr_eval(self, globalns, localns, *args, **kwargs)
        typing.ForwardRef._evaluate = _patched_forward_ref
