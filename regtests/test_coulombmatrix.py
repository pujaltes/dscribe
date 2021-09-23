import pytest
import numpy as np
import sparse
from ase.build import molecule
from conftest import (
    check_symmetry_rotation,
    check_symmetry_translation,
    check_derivatives_include,
    check_derivatives_exclude,
    check_derivatives_numerical,
)
from dscribe.descriptors import CoulombMatrix


def cm_python(system, n_atoms_max, permutation, flatten):
    """Calculates a python reference value for the Coulomb matrix.
    """
    Z = system.get_atomic_numbers()
    pos = system.get_positions()
    distances = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
    n = len(system)
    cm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                cm[i, j] = 0.5 * Z[i]**2.4
            else:
                cm[i, j] = Z[i] * Z[j] / distances[i, j]
    if permutation == "eigenspectrum":
        eigenvalues = np.linalg.eigvalsh(cm)
        abs_values = np.absolute(eigenvalues)
        sorted_indices = np.argsort(abs_values)[::-1]
        eigenvalues = eigenvalues[sorted_indices]
        padded = np.zeros((n_atoms_max))
        padded[:n] = eigenvalues
    elif flatten:
        cm = cm.flatten()
        padded = np.zeros((n_atoms_max**2))
        padded[:n**2] = cm
    else:
        padded = np.zeros((n_atoms_max, n_atoms_max))
        padded[:n, :n] = cm
    return padded


def test_exceptions(H2O):
    # Unknown permutation option
    with pytest.raises(ValueError):
        CoulombMatrix(n_atoms_max=5, permutation="unknown")
    # Negative n_atom_max
    with pytest.raises(ValueError):
        CoulombMatrix(n_atoms_max=-1)
    # System has more atoms that the specifed maximum
    with pytest.raises(ValueError):
        cm = CoulombMatrix(n_atoms_max=2)
        cm.create([H2O])


def test_number_of_features():
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=False)
    n_features = desc.get_number_of_features()
    assert n_features == 25


def test_periodicity(bulk):
    """Tests that periodicity is not taken into account in Coulomb matrix
    even if the system is set as periodic.
    """
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=False)
    cm = desc.create(bulk)
    pos = bulk.get_positions()
    assumed = 1 * 1 / np.linalg.norm((pos[0] - pos[1]))
    assert cm[0, 1] == assumed


def test_features(H2O):
    # No permutation handling
    n_atoms_max = 5
    desc = CoulombMatrix(n_atoms_max=n_atoms_max, permutation="none")
    n_features = desc.get_number_of_features()
    cm = desc.create(H2O)
    assert n_features == n_atoms_max**2
    cm_assumed = cm_python(H2O, n_atoms_max, "none", True)
    assert np.allclose(cm, cm_assumed)

    # Eigen spectrum
    desc = CoulombMatrix(n_atoms_max=n_atoms_max, permutation="eigenspectrum")
    n_features = desc.get_number_of_features()
    cm = desc.create(H2O)
    assert n_features == n_atoms_max
    cm_assumed = cm_python(H2O, n_atoms_max, "eigenspectrum", True)
    assert np.allclose(cm, cm_assumed)

    # Random
    desc = CoulombMatrix(n_atoms_max=n_atoms_max, permutation="random", sigma=0.1, seed=42)
    n_features = desc.get_number_of_features()
    assert n_features == n_atoms_max**2


def test_flatten(H2O):
    # Unflattened
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=False)
    cm_unflattened = desc.create(H2O)
    assert cm_unflattened.shape == (5, 5)

    # Flattened
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=True)
    cm_flattened = desc.create(H2O)
    assert cm_flattened.shape == (25,)

    # Check that flattened and unflattened versions contain same values
    assert np.array_equal(cm_flattened[:9], cm_unflattened[:3, :3].ravel())
    assert np.all((cm_flattened[9:] == 0))
    cm_unflattened[:3, :3] = 0
    assert np.all((cm_unflattened == 0))


def test_sparse(H2O):
    # Dense
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=True, sparse=False)
    vec = desc.create(H2O)
    assert type(vec) == np.ndarray

    # Sparse
    desc = CoulombMatrix(n_atoms_max=5, permutation="none", flatten=True, sparse=True)
    vec = desc.create(H2O)
    assert type(vec) == sparse.COO


@pytest.mark.parametrize(
    "n_jobs, flatten, sparse",
    [
        (1, True, False),  # Serial job, flattened, dense
        (2, True, False),  # Parallel job, flattened, dense
        (2, False, False),  # Unflattened output, dense
        (1, True, True),  # Serial job, flattened, sparse
        (2, True, True),  # Parallel job, flattened, sparse
        (2, False, True),  # Unflattened output, sparse
    ],
)
def test_parallel(n_jobs, flatten, sparse):
    """Tests creating dense output parallelly."""
    samples = [molecule("CO"), molecule("N2O")]
    n_atoms_max = 5
    desc = CoulombMatrix(
        n_atoms_max=n_atoms_max, permutation="none", flatten=flatten, sparse=sparse
    )
    n_features = desc.get_number_of_features()

    output = desc.create(system=samples, n_jobs=n_jobs)
    assumed = (
        np.empty((2, n_features))
        if flatten
        else np.empty((2, n_atoms_max, n_atoms_max))
    )
    a = desc.create(samples[0])
    b = desc.create(samples[1])
    if sparse:
        output = output.todense()
        a = a.todense()
        b = b.todense()
    assumed[0, :] = a
    assumed[1, :] = b
    assert np.allclose(output, assumed)


def descriptor_for_system(systems):
    n_atoms_max = max([len(s) for s in systems])
    desc = CoulombMatrix(n_atoms_max=n_atoms_max, permutation="none", flatten=True)
    return desc


def test_symmetries():
    """Tests the symmetries of the descriptor."""
    check_symmetry_translation(descriptor_for_system)
    check_symmetry_rotation(descriptor_for_system)


def test_derivatives():
    methods = ["numerical"]
    check_derivatives_include(descriptor_for_system, methods)
    check_derivatives_exclude(descriptor_for_system, methods)
    check_derivatives_numerical(descriptor_for_system)
