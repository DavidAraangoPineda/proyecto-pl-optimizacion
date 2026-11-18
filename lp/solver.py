"""Punto de entrada del motor: resuelve un problema con el método elegido."""
from .analysis import interpret
from .bigm import solve_bigm
from .revised import solve_revised
from .standard import build_standard_form

METHODS = {"bigm": ("Gran M (tablero)", solve_bigm), "revised": ("Simplex revisado", solve_revised)}


def solve(problem, method="bigm"):
    sf = build_standard_form(problem)
    run = METHODS[method][1](sf)
    return interpret(problem, sf, run)
