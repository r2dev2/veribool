import re
from typing import Callable, NamedTuple

dbg = False


def set_dbg(new_dbg):
    global dbg
    dbg = new_dbg


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
Binop -> ^
Binop -> xor
Binop -> xnor
Var -> [a-zA-Z]+
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
        if text[i] == "^":
            tokens.append(Binop("xor"))
            i += 1
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

        return black.format_str(code, mode=black.Mode()).strip()
    except ImportError:
        return code


def full_compile(expr: str) -> tuple[list[str], Callable]:
    tokens = lex(expr)
    p = Parser(tokens)
    r = p.parse_expr()
    comp = prettify(compile_bexpr(r))
    variables = sorted(set(v.val for v in tokens if isinstance(v, Variable)))
    pycode = f"lambda {', '.join(variables)}, **_kwargs: {comp}"
    if dbg:
        print(pycode)
    return variables, eval(pycode)


def expr_to_python(expr: str) -> Callable:
    return full_compile(expr)[1]
