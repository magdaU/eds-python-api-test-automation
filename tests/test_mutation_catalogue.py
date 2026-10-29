import importlib.util
from pathlib import Path

from tests.support.allure_labels import labels

pytestmark = labels("Test support", "Mutation checks")

ROOT = Path(__file__).resolve().parents[1]


def load_mutation_script():
    spec = importlib.util.spec_from_file_location("mutation_check", ROOT / "scripts" / "mutation_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_whenCheckingTheMutationCatalogue_thenEveryMutationMatchesExactlyOneLineOfItsSource():
    # arrange
    mutations = load_mutation_script().MUTATIONS

    # act
    stale = [m.name for m in mutations if (ROOT / m.path).read_text(encoding="utf-8").count(m.old) != 1]

    # assert
    assert stale == []
    assert len({m.name for m in mutations}) == len(mutations)
