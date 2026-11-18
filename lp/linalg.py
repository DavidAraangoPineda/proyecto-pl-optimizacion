"""Álgebra lineal exacta con Fractions (sin numpy)."""
from fractions import Fraction


def identity(m):
    return [[Fraction(int(i == j)) for j in range(m)] for i in range(m)]


def inverse(M):
    """Inversa por Gauss-Jordan. Lanza ValueError si es singular."""
    m = len(M)
    aug = [list(map(Fraction, row)) + identity(m)[i] for i, row in enumerate(M)]
    for col in range(m):
        piv = next((r for r in range(col, m) if aug[r][col] != 0), None)
        if piv is None:
            raise ValueError("Matriz singular")
        aug[col], aug[piv] = aug[piv], aug[col]
        p = aug[col][col]
        aug[col] = [v / p for v in aug[col]]
        for r in range(m):
            if r != col and aug[r][col] != 0:
                f = aug[r][col]
                aug[r] = [a - f * b for a, b in zip(aug[r], aug[col])]
    return [row[m:] for row in aug]


def matvec(M, v):
    return [sum((a * b for a, b in zip(row, v)), Fraction(0)) for row in M]


def column(A, j):
    return [row[j] for row in A]
