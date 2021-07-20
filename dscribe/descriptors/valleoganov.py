from dscribe.descriptors import MBTR
import math

class ValleOganov(MBTR):
    """Shortcut for implementing the fingerprint descriptor by Valle and Oganov
    for :math:`k=2` and :math:`k=3` using MBTR. Automatically uses the right
    weightings and normalizes the output.

    You can choose which terms to include by providing a dictionary in the
    k2 or k3 arguments. This dictionary should contain information
    under three keys: "sigma", "n" and "r_cutoff".
    """

    def __init__(
        self,
        species,
        periodic,
        k2=None,
        k3=None,
        flatten=True,
        sparse=False,
    ):

        """
        Args:
            species (iterable): The chemical species as a list of atomic
                numbers or as a list of chemical symbols. Notice that this is not
                the atomic numbers that are present for an individual system, but
                should contain all the elements that are ever going to be
                encountered when creating the descriptors for a set of systems.
                Keeping the number of chemical species as low as possible is
                preferable.
            periodic (bool): Set to true if you want the descriptor output to
                respect the periodicity of the atomic systems (see the
                pbc-parameter in the constructor of ase.Atoms).

            k2 (dict): Dictionary containing the setup for the k=2 term.
                Contains setup for the discretization and radial cutoff.
                For example::

                    k2 = {
                        "sigma": 0.1,
                        "n": 50,
                        "r_cutoff": 10
                    }

            k3 (dict): Dictionary containing the setup for the k=3 term.
                Contains setup for the discretization and radial cutoff.
                For example::

                    k3 = {
                        "sigma": 0.1,
                        "n": 50,
                        "r_cutoff": 10
                    }

            flatten (bool): Whether the output should be flattened to a 1D
                array. If False, a dictionary of the different tensors is
                provided, containing the values under keys: "k1", "k2", and
                "k3":
            sparse (bool): Whether the output should be a sparse matrix or a
                dense numpy array.
        """

    # Check that k2 has all the valid keys and only them
        if k2 is not None:
            for key in k2.keys():
                valid_keys = set(("sigma", "n", "r_cutoff"))
                if key not in valid_keys:
                    raise ValueError(
                        f"The given setup contains the following invalid key: {key}"
                    )
            for key in valid_keys:
                if key not in k2.keys():
                    raise ValueError(
                        f"Missing value for {key}"
                    )
        
    # Check that k3 has all the valid keys and only them
        if k3 is not None:
            for key in k3.keys():
                valid_keys = set(("sigma", "n", "r_cutoff"))
                if key not in valid_keys:
                    raise ValueError(
                        f"The given setup contains the following invalid key: {key}"
                    )
            for key in valid_keys:
                if key not in k3.keys():
                    raise ValueError(
                        f"Missing value for {key}"
                    )

        if k2 is not None:
            # n = k2["r_cutoff"] / k2["delta"] + 1
            # kasvata r_cutoff niin että n on int
            # tai muuta deltaa samalla tavalla
            # tai sitten deltan on pakko olla sellanen että n on tasaluku?
            # tai ei deltaa ollenkaan????
            k2_temp = {
                "geometry": {"function": "distance"},
                "grid": {"min": 0, "max": k2["r_cutoff"], "sigma": k2["sigma"], "n": k2["n"]},
                "weighting": {"function": "inverse_square", "r_cutoff": k2["r_cutoff"]},
            }
        else:
            k2_temp = None

        if k3 is not None:
            # n = k2["r_cutoff"] / k2["delta"] + 1
            k3_temp = {
                "geometry": {"function": "angle"},
                "grid": {"min": 0, "max": 180, "sigma": k3["sigma"], "n": k3["n"]},
                "weighting": {"function": "smooth_cutoff", "r_cutoff": k3["r_cutoff"]},
            }
        else:
            k3_temp = None
        
        # muista gamma
        # mieluummin KeyError ku ValueError parametreille?

        super().__init__(
            species=species, 
            periodic=periodic, 
            k1=None, 
            k2=k2_temp, 
            k3=k3_temp, 
            flatten=flatten, 
            sparse=sparse,
            normalization="valle_oganov",
            normalize_gaussians=True
            )
