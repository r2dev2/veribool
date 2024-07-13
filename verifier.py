import re
from typing import Callable, NamedTuple

class Variable(NamedTuple):
    val: str

class LeftParen(NamedTuple):
    pass

class RightParen(NamedTuple):
    pass

class Not(NamedTuple):
    pass

class Binop(NamedTuple):
    op: str

class Node(tuple):
    @classmethod
    def new(cls, *args):
        return cls([cls, *args])

    def __repr__(self):
        cls, *rest = self
        return f"{cls.__name__}{repr(tuple(rest))}"

class Expr(Node):
    """
    Either (Not, Expr), (Expr, Binop, Expr), (Term, Binop, Expr) or (Term).
    """
    pass

class Term(Node):
    """
    Tuple of (MaybeVar | Expr, Term) or (MaybeVar | Expr) to be ANDed together
    """

class MaybeVar(Node):
    """
    Either (Variable, Not) or (Variable)
    """
    pass

"""
Expr -> Term Binop Expr
Expr -> Term
Term -> ( Expr ) ' Term
Term -> ( Expr ) Term
Term -> MaybeVar Term
Term -> MaybeVar
MaybeVar -> Var
MaybeVar -> Var '
Binop -> +
Binop -> xor
Binop -> xnor
Var -> [a-zA-Z]
"""

def lex(text: str):
    text = re.sub(r"\s+", "", text)
    tokens = []
    i = 0
    while i < len(text):
        if text.startswith("xnor", i):
            tokens.append(Binop("xnor"))
            i += len("xnor")
            continue
        if text.startswith("xor", i):
            tokens.append(Binop("xor"))
            i += len("xor")
            continue
        if text[i] == "+":
            tokens.append(Binop("or"))
            i += 1
            continue
        if text[i] == "'":
            tokens.append(Not())
            i += 1
            continue
        if text[i] == "(":
            tokens.append(LeftParen())
            i += 1
            continue
        if text[i] == ")":
            tokens.append(RightParen())
            i += 1
            continue
        if text[i].isalpha():
            tokens.append(Variable(text[i]))
            i += 1
            continue
        raise SyntaxError(f"Unexpected token {repr(text[i])}")
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens[::-1]

    def parse_expr(self):
        match self.peek():
            case Variable(_) | LeftParen():
                term = self.parse_term()
                if isinstance(self.peek(), Binop):
                    return Expr.new(term, self.eat(Binop), self.parse_expr())
                return Expr.new(term)
            case n:
                raise SyntaxError(f"Expected Variable, got {n}")

    def parse_term(self):
        match self.peek():
            case LeftParen():
                self.eat(LeftParen)
                expr = self.parse_expr()
                self.eat(RightParen)
                if isinstance(self.peek(), Not):
                    expr = Expr.new(self.eat(Not), expr)
                if isinstance(self.peek(), LeftParen | Variable):
                    return Term.new(expr, self.parse_term())
                return Term.new(expr)

            case Variable(val_):
                mvar = self.parse_maybe_var()
                if isinstance(self.peek(), LeftParen | Variable):
                    return Term.new(mvar, self.parse_term())
                return Term.new(mvar)
            case n:
                raise SyntaxError(f"Expected Variable, got {n}")

    def parse_maybe_var(self):
        match self.peek():
            case Variable(val_):
                var = self.eat(Variable)
                if isinstance(self.peek(), Not):
                    return MaybeVar.new(var, self.eat(Not))
                return MaybeVar.new(var)

    def eat(self, token, eq=False):
        if (not eq) and not isinstance(self.peek(), token):
            raise SyntaxError("Incorrect syntax in expression")
        if eq and not self.peek() == token:
            raise SyntaxError("Incorrect syntax in expression")
        return self.next()

    def eof(self):
        if self.ntokens() != 0:
            raise SyntaxError("Tokens left over!")

    def ntokens(self):
        return len(self.tokens)

    def peek(self):
        if self.ntokens() == 0:
            return None
        return self.tokens[-1]

    def next(self):
        return self.tokens.pop()

def compile_bexpr(expr: Node) -> str:
    """
    Compiles an expression to corresponding Python code.
    """
    match expr:
        case Expr((_, x, y, z)):
            xc = compile_bexpr(x)
            if isinstance(x, Term):
                xc = f"({xc})"
            zc = compile_bexpr(z)
            if y.op == "or":
                return f"({xc} or {zc})"
            if y.op == "xor":
                return f"({xc} ^ {zc})"
            if y.op == "xnor":
                return f"(not ({xc} ^ {zc}))"
            raise ValueError(f"Unsupported {y.op}")
        case Expr((_, Not(), y)):
            return f"(not {compile_bexpr(y)})"
        case Expr((_, term)):
            return f"({compile_bexpr(term)})"
        case Term((_, mv)):
            return compile_bexpr(mv)
        case Term((_, mv, term)):
            return f"{compile_bexpr(mv)} and {compile_bexpr(term)}"
        case MaybeVar((_, var, Not())):
            return f"(not {var.val})"
        case MaybeVar((_, var)):
            return var.val
        case _:
            return ""

def prettify(code: str) -> str:
    try:
        import black
        return black.format_str(
            code, mode=black.Mode()
        ).strip()
    except ImportError:
        return code

expr = "(xy)' + yz xor xy'"
def full_compile(expr: str) -> tuple[list[str], Callable]:
    tokens = lex(expr)
    # print(tokens)
    p = Parser(tokens)
    r = p.parse_expr()
    comp = prettify(compile_bexpr(r))
    variables = sorted(set(v.val for v in tokens if isinstance(v, Variable)))
    variables.append("**_")
    pycode = f"lambda {', '.join(variables)}: {comp}"
    # print(variables)
    print(pycode)
    return variables, eval(pycode)

def expr_to_python(expr: str) -> Callable:
    return full_compile(expr)[1]

# e1 = "x'y' + x'z' + xyz"
# e2 = "x xnor yz"
# vnames, fn1 = expr_to_python(e1)
# _, fn2 = expr_to_python(e2)
#
# bn = [False, True]
# for x in bn:
#     for y in bn:
#         for z in bn:
#             assert fn1(x=x, y=y, z=z) == fn2(x=x, y=y, z=z)

fn = expr_to_python("(w)'(x + y) + wx'y'")
# fn = expr_to_python("w xor (x + y)")
# fn = lambda w, x, y, z: ((not w) and (x or y)) or (w and (not x) and (not y))
bn = [False, True]
for w in bn:
    for x in bn:
        for y in bn:
            for z in bn:
                r = fn(w=w, x=x, y=y, z=z)
                if r:
                    print([*map(int, [w, x, y, z])])
exit()

# note: it won't work with paren at start of term
ea = "w(x + yz)"
eb = "x xnor yz"
ec = "y xor z"
ed = "z'"
fa, fb, fc, fd = map(expr_to_python, [ea, eb, ec, ed])
vnames = [*"wxyz"]

def dectobin(d: int, vnames: list[str]) -> dict[str, bool]:
    if d < 0 or d >= (1 << len(vnames)):
        raise ValueError(f"Integer {d} outside of {len(vnames)}-bit uint range")
    b = bin(d)[2:].zfill(len(vnames))
    b_bool = [n == "1" for n in b]
    return dict(zip(vnames, b_bool))

def bintodec(bits: list[bool]) -> int:
    return int("".join("1" if b else "0" for b in bits), 2)

for n in range(10):
    inp = dectobin(n + 3, vnames)
    out = [
        fa(**inp),
        fb(**inp),
        fc(**inp),
        fd(**inp)
    ]
    print(bintodec(out))
