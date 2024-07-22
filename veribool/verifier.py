import itertools as it
from typing import Callable, NamedTuple

from .compiler import full_compile


class Divergence(NamedTuple):
    inputs: list[bool]
    value_1: bool
    value_2: bool

    def __str__(self):
        return f"{[*map(int, self.inputs)]} - {self.value_1} vs {self.value_2}"


class TableEntry(NamedTuple):
    inputs: list[bool]
    value: bool

    def __str__(self):
        return f"{[*map(int, self.inputs)]} - {self.value}"


def generate_truth_table(expr: str) -> list[TableEntry]:
    vnames, fn = full_compile(expr)
    return __generate_truth_table(vnames, fn)


def find_divergence(expr1: str, expr2: str) -> Divergence | None:
    vnames_1, fn1 = full_compile(expr1)
    vnames_2, fn2 = full_compile(expr2)
    vnames = sorted({*vnames_1, *vnames_2})
    if len(vnames) > 20:
        raise NotImplementedError("Solving with > 20 inputs needs z3 - will implement")

    truth_1 = __generate_truth_table(vnames, fn1)
    truth_2 = __generate_truth_table(vnames, fn2)
    for e1, e2 in zip(truth_1, truth_2):
        if e1 != e2:
            assert e1.inputs == e2.inputs, "somehow inputs were tested in diff order..."
            return Divergence(e1.inputs, e1.value, e2.value)
    return None


def __generate_truth_table(
    vnames: list[str], fn: Callable[..., bool]
) -> list[TableEntry]:
    bn = [[False, True] for _ in vnames]
    table = []
    for inpl in it.product(*bn):
        inp_dict = dict(zip(vnames, inpl))
        table.append(TableEntry(list(inpl), bool(fn(**inp_dict))))
    return table


# ea = "w(x + yz)"
# eb = "x xnor yz"
# ec = "y xor z"
# ed = "z'"
# fa, fb, fc, fd = map(expr_to_python, [ea, eb, ec, ed])
# vnames = [*"wxyz"]


def dectobin(d: int, vnames: list[str]) -> dict[str, bool]:
    if d < 0 or d >= (1 << len(vnames)):
        raise ValueError(f"Integer {d} outside of {len(vnames)}-bit uint range")
    b = bin(d)[2:].zfill(len(vnames))
    b_bool = [n == "1" for n in b]
    return dict(zip(vnames, b_bool))


def bintodec(bits: list[bool]) -> int:
    return int("".join("1" if b else "0" for b in bits), 2)


# for n in range(10):
#     inp = dectobin(n + 3, vnames)
#     out = [
#         fa(**inp),
#         fb(**inp),
#         fc(**inp),
#         fd(**inp)
#     ]
#     print(bintodec(out))
