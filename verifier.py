import re
from typing import NamedTuple

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
    Either (Term, Binop, Expr) or (Term).
    """
    pass

class Term(Node):
    """
    Tuple of MaybeVar to be ANDed together.
    """

class MaybeVar(Node):
    """
    Either (Variable, Not) or (Variable)
    """
    pass

"""
Expr -> ( Expr ) '
Expr -> ( Expr )
Expr -> ( Expr ) ' Binop Expr
Expr -> ( Expr ) Binop Expr
Expr -> Term Binop Expr
Expr -> Term
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
            case LeftParen():
                self.eat(LeftParen)
                expr = self.parse_expr()
                self.eat(RightParen)
                if isinstance(self.peek(), Not):
                    expr = Expr.new(self.eat(Not), expr)
                if isinstance(self.peek(), Binop):
                    return Expr.new(expr, self.eat(Binop), self.parse_expr())
                return expr
            case Variable(val_):
                term = self.parse_term()
                if isinstance(self.peek(), Binop):
                    return Expr.new(term, self.eat(Binop), self.parse_expr())
                return Expr.new(term)
            case n:
                raise SyntaxError(f"Expected Variable, got {n}")

    def parse_term(self):
        match self.peek():
            case Variable(val_):
                mvar = self.parse_maybe_var()
                if not isinstance(self.peek(), Variable):
                    return Term.new(mvar)
                return Term.new(mvar, self.parse_term())
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

tokens = lex("(xy) + yz xor ab'")
# print(tokens)
p = Parser(tokens)
print(p.parse_expr())
