import ase
from ase.calculators.lj import LennardJones
import numpy as np
from dscribe.descriptors import SOAP
import matplotlib.pyplot as plt

# Setting up the SOAP descriptor
soap = SOAP(
    species=["H"],
    periodic=False,
    rcut=5.0,
    sigma=0.5,
    nmax=3,
    lmax=0,
)

# Generate dataset of Lennard-Jones energies and forces
n_samples = 200
traj = []
n_atoms = 2
energies = np.zeros(n_samples)
forces = np.zeros((n_samples, n_atoms, 3))
r = np.linspace(2.5, 5.0, n_samples)
for i, d in enumerate(r):
    a = ase.Atoms('HH', positions = [[-0.5 * d, 0, 0], [0.5 * d, 0, 0]])
    a.set_calculator(LennardJones(epsilon=1.0 , sigma=2.9))
    traj.append(a)
    energies[i] = a.get_total_energy()
    forces[i, :, :] = a.get_forces()
	
# Plot the energies to validate them
fig, ax = plt.subplots(figsize=(8, 5))
plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
line, = ax.plot(r, energies)
plt.xlabel("Distance (Å)")
plt.ylabel("Energy (eV)")
plt.show()

# Create SOAP output for all samples. One center is chosen to be directly
# between the atoms.
center = [0, 0, 0]
descriptors = []
derivatives = []
for t in traj:
    i_derivative, i_descriptor = soap.derivatives_single(t, positions=[center], method="numerical")
    descriptors.append(i_descriptor[0])
    derivatives.append(i_derivative[0])
descriptors = np.array(descriptors)
derivatives = np.array(derivatives)

# Save to disk for later training
np.save("r.npy", r)
np.save("E.npy", energies)
np.save("D.npy", descriptors)
np.save("dD_dr.npy", derivatives)
np.save("F.npy", forces)
