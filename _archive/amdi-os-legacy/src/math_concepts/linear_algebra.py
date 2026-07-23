'''
AEGIS-MIOS — Linear Algebra
============================
Matrix decomposition algorithms:
- Gram-Schmidt QR Decomposition
- Cholesky Decomposition (A = L L^T)
- Jacobi Eigenvalue Algorithm (Symmetric matrices)
- Singular Value Decomposition (SVD)
'''

from __future__ import annotations

import numpy as np


def qr_decomposition(A: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    '''
    Compute QR decomposition using Modified Gram-Schmidt process.
    A = Q R
    '''
    m, n = A.shape
    Q = np.zeros((m, n))
    R = np.zeros((n, n))

    for j in range(n):
        v = A[:, j].copy()
        for i in range(j):
            R[i, j] = np.dot(Q[:, i], A[:, j])
            v = v - R[i, j] * Q[:, i]
        R[j, j] = np.linalg.norm(v)
        if R[j, j] > 1e-12:
            Q[:, j] = v / R[j, j]
        else:
            Q[:, j] = np.zeros(m)
    return Q, R


def cholesky_decomposition(A: np.ndarray) -> np.ndarray:
    '''
    Compute Cholesky decomposition of a symmetric positive-definite matrix A.
    A = L L.T
    '''
    n = A.shape[0]
    L = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1):
            sum_val = np.sum(L[i, :j] * L[j, :j])
            if i == j:
                val = A[i, i] - sum_val
                L[i, j] = np.sqrt(max(val, 0.0))
            else:
                if L[j, j] > 0:
                    L[i, j] = (A[i, j] - sum_val) / L[j, j]
                else:
                    L[i, j] = 0.0
    return L


def jacobi_eigen(A: np.ndarray, max_iter: int = 100, tol: float = 1e-9) -> tuple[np.ndarray, np.ndarray]:
    '''
    Compute eigenvalues and eigenvectors of a symmetric matrix A using Jacobi rotation.
    Returns (eigenvalues, eigenvectors).
    '''
    n = A.shape[0]
    V = np.eye(n)
    A_rot = A.copy()

    for _ in range(max_iter):
        # Find the largest off-diagonal element
        p, q = 0, 1
        max_val = abs(A_rot[0, 1])
        for i in range(n):
            for j in range(i + 1, n):
                if abs(A_rot[i, j]) > max_val:
                    max_val = abs(A_rot[i, j])
                    p, q = i, j

        if max_val < tol:
            break

        # Compute rotation angle theta
        if abs(A_rot[p, p] - A_rot[q, q]) < 1e-15:
            theta = np.pi / 4.0
        else:
            phi = 2.0 * A_rot[p, q] / (A_rot[q, q] - A_rot[p, p])
            theta = 0.5 * np.arctan(phi)

        c = np.cos(theta)
        s = np.sin(theta)

        # Apply Givens rotation to A_rot: J.T * A_rot * J
        J = np.eye(n)
        J[p, p] = c
        J[q, q] = c
        J[p, q] = s
        J[q, p] = -s

        A_rot = J.T @ A_rot @ J
        V = V @ J

    eigenvalues = np.diagonal(A_rot)
    # Sort descending
    idx = np.argsort(eigenvalues)[::-1]
    return eigenvalues[idx], V[:, idx]


def singular_value_decomposition(A: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Compute Singular Value Decomposition of matrix A: A = U S V.T
    using eigenvalues of A.T A (for V) and A A.T (for U).
    '''
    m, n = A.shape
    ATA = A.T @ A

    # V are eigenvectors of A.T A
    eigvals_v, V = jacobi_eigen(ATA)
    # Filter negative/tiny eigenvalues
    eigvals_v = np.maximum(eigvals_v, 0.0)
    s = np.sqrt(eigvals_v)

    # Sort singular values and corresponding vectors V
    sort_idx = np.argsort(s)[::-1]
    s = s[sort_idx]
    V = V[:, sort_idx]

    # Compute U
    U = np.zeros((m, m))
    # Rank of A
    rank = np.sum(s > 1e-12)

    for i in range(min(rank, m, n)):
        if s[i] > 1e-12:
            U[:, i] = (A @ V[:, i]) / s[i]

    # Fill remaining columns of U using Gram-Schmidt if needed (to ensure orthogonal matrix)
    if rank < m:
        # Generate random vectors and orthogonalize them against existing columns
        for i in range(rank, m):
            v = np.random.rand(m)
            for j in range(i):
                v -= np.dot(U[:, j], v) * U[:, j]
            v_norm = np.linalg.norm(v)
            if v_norm > 1e-12:
                U[:, i] = v / v_norm

    return U, s[:min(m, n)], V.T
