/*Copyright 2019 DScribe developers

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
#include "cm.h"
#include "celllist.h"
#include "geometry.h"
#include <math.h>
#include "jacobi_pd.h"

using namespace std;

CoulombMatrix::CoulombMatrix(
    unsigned int n_atoms_max,
    string permutation,
    double sigma,
    int seed
)
    : DescriptorGlobal(false)
    , n_atoms_max(n_atoms_max)
    , permutation(permutation)
    , sigma(sigma)
    , seed(seed)
{
}

void CoulombMatrix::create_raw(
    py::array_t<double> out, 
    py::array_t<double> positions,
    py::array_t<int> atomic_numbers,
    CellList &cell_list
) const
{
    // Calculate all pairwise distances.
    py::array_t<double> matrix = distances(positions);
    auto matrix_mu = matrix.mutable_unchecked<2>();
    auto out_mu = out.mutable_unchecked<1>();
    auto atomic_numbers_u = atomic_numbers.unchecked<1>();

    // Construct matrix
    int n_atoms = atomic_numbers.shape(0);
    for (int i = 0; i < n_atoms; ++i) {
        for (int j = i; j < n_atoms; ++j) {
            if (j == i) {
                matrix_mu(i, j) = 0.5 * pow(atomic_numbers_u(i), 2.4);
            } else {
                double value = atomic_numbers_u(i) * atomic_numbers_u(j) / matrix_mu(i, j);
                matrix_mu(i, j) = value;
                matrix_mu(j, i) = value;
            }
        }
    }

    // Handle the permutation option
    if (this->permutation == "eigenspectrum") {
        this->getEigenspectrum(matrix, out, n_atoms);
    } else {
        if (this->permutation == "sorted") {
            this->sort(matrix);
        } else if (this->permutation == "random") {
            this->sortRandomly(matrix);
        }
        // Flatten
        int k = 0;
        for (int i = 0; i < n_atoms; ++i) {
            for (int j = 0; j < n_atoms; ++j) {
                out_mu(k) = matrix_mu(i, j);
                ++k;
            }
        }
    }
}

void CoulombMatrix::getEigenspectrum(
    py::array_t<double> matrix,
    py::array_t<double> out,
    int n_atoms
) const
{
    // Calculate eigenvalues using the jacobi_pd library: it is a very
    // lightweight, open-source library for solving eigenvalue problems.
    vector<double> eigenvalues(n_atoms);
    auto matrix_mu = matrix.mutable_unchecked<2>();
    vector<vector<double>> eigenvectors(n_atoms, vector<double>(n_atoms));
    vector<vector<double>> matrix_cpp(n_atoms, vector<double>(n_atoms));
    for (int i = 0; i < n_atoms; ++i) {
        for (int j = i; j < n_atoms; ++j) {
            matrix_cpp[i][j] = matrix_mu(i, j);
        }
    }
    jacobi_pd::Jacobi<double, vector<double>&, vector<vector<double>>&, const vector<vector<double>>&> eigen_calc(n_atoms);
    eigen_calc.Diagonalize(matrix_cpp, eigenvalues, eigenvectors);

    // Sort the values in descending order by absolute value
    std::sort(
        eigenvalues.begin(),
        eigenvalues.end(),
        [ ]( const double& lhs, const double& rhs ) {
            return abs(lhs) > abs(rhs);
        }
    );

    // Copy to output
    auto out_mu = out.mutable_unchecked<1>();
    for (int i = 0; i < n_atoms; ++i) {
        out_mu[i] = eigenvalues[i];
    }
}

void CoulombMatrix::sort(
    py::array_t<double> matrix
) const
{
}

void CoulombMatrix::sortRandomly(
    py::array_t<double> matrix
) const
{
}

int CoulombMatrix::get_number_of_features() const
{
    return this->permutation == "eigenspectrum"
        ? this->n_atoms_max
        : this->n_atoms_max * this->n_atoms_max;
}
