"""Regression tests for repository-local evaluation package imports."""
from importlib import import_module
from pathlib import Path


def test_evaluation_package_resolves_to_repository() -> None:
    package = import_module("evaluation")
    package_file = getattr(package, "__file__", None)
    # An explicit package marker should make this a regular package.
    assert package_file is not None
    repo_root = Path(__file__).resolve().parents[1]
    resolved = Path(package_file).resolve()
    assert resolved.is_relative_to(repo_root)


def test_evaluation_runner_modules_import() -> None:
    modules = (
        "evaluation.scripts.evaluate_extraction",
        "evaluation.scripts.evaluate_packing",
        "evaluation.scripts.evaluate_privacy",
        "evaluation.scripts.evaluate_retrieval",
        "evaluation.scripts.run_all",
    )
    for module in modules:
        assert import_module(module) is not None
