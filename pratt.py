#!/usr/bin/env python3

import re
import sys
from operator import mul, add, sub, ifloordiv, pow


class Lexer():
    def __init__(self, tokens):
        self.tokens = tokens

    def next(self):
        return self.tokens.pop(0)

    def peek(self):
        return self.tokens[0]

    def expect(self, val_type):
        next_val = self.next()
        if not isinstance(next_val, val_type):
            raise ValueError(f"expected {val_type}, got {next_val}")


def operator_name(op):
    if hasattr(op, "__name__"):
        return op.__name__
    return repr(op)


class UnitNode():
    def __init__(self, operator, param):
        self.operator = operator
        self.param = param

    def __repr__(self):
        return f"({operator_name(self.operator)} {repr(self.param)})"


class Node():
    def __init__(self, operator, *args):
        self.operator = operator
        self.args = args

    def __repr__(self):
        args_repr = ' '.join(map(repr, self.args))
        return f"({operator_name(self.operator)} {args_repr})"


class CallNode():
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

    def __repr__(self):
        args_repr = ', '.join(repr(arg) for arg in self.args)
        return f"{self.func_name}({args_repr})"


def infix(func):
    class InfixOperator():
        def handle_left(self, parser, left):
            return Node(func, left, parser.parse(self.prio))
    return InfixOperator


def infixr(func):
    class InfixROperator():
        def handle_left(self, parser, left):
            return Node(func, left, parser.parse(self.prio - 1))
    return InfixROperator


class Token():
    prio = 0

    handle_nul = None
    handle_left = None

    def __repr__(self):
        return f"<{self.value}>"


class EOF(Token):
    def __repr__(self):
        return "EOF"


class ID(Token):
    def __init__(self, value):
        self.value = value

    def handle_nul(self, parser):
        return self.value


class Num(Token):
    def __init__(self, value):
        self.value = value

    def handle_nul(self, parser):
        return self.value


class ConstToken(Token):
    tok_map = {}
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.tok_map[cls.value] = cls


class RParen(ConstToken):
    value = ')'


class Comma(ConstToken):
    value = ','


class LParen(ConstToken):
    prio = 80
    value = '('

    def handle_nul(self, parser):
        res = parser.parse()
        lexer.expect(RParen)
        return res

    def handle_left(self, parser, left):
        assert isinstance(left, str), "cannot invoke expression as a function"
        args = []
        while True:
            if isinstance(lexer.peek(), RParen):
                lexer.next()
                break
            args.append(parser.parse())
            lexer.expect(Comma)
        return CallNode(left, args)


class Plus(infix(add), ConstToken):
    prio = 10
    value = '+'

    def handle_nul(self, parser):
        return parser.parse(self.prio)


class Minus(infix(sub), ConstToken):
    prio = 10
    value = '-'

    def handle_nul(self, parser):
        return UnitNode('-', parser.parse(self.prio))


class Div(infix(ifloordiv), ConstToken):
    prio = 20
    value = '/'


class Mult(infix(mul), ConstToken):
    prio = 30
    value = '*'


class Exp(infixr(pow), ConstToken):
    prio = 40
    value = '^'


class Parser():
    def __init__(self):
        self.depth = 0

    @property
    def padding(self):
        return "  " * self.depth

    def nud(self, token):
        print(f"{self.padding}nul({token})")
        return token.handle_nul(self)

    def led(self, left, token):
        print(f"{self.padding}led({token})")
        left_handler = token.handle_left
        if left_handler is None:
            raise ValueError(f"{token} isn't an operator")
        return left_handler(self, left)

    def parse(self, up_prio=0):
        print(f"{self.padding}parse({up_prio})")
        self.depth += 1
        left = self.nud(lexer.next())
        while lexer.peek().prio > up_prio:
            left = self.led(left, lexer.next())
        self.depth -= 1
        print(f"{self.padding}<=")
        return left


TOKEN_SPLITTER = re.compile(r" |(\w+|\(|\))")


def tokenize(line):
    for token in re.split(TOKEN_SPLITTER, line):
        if token is not None:
            token = token.strip()

        if not token:
            continue

        const_tok_cls = ConstToken.tok_map.get(token, None)
        if const_tok_cls is not None:
            yield const_tok_cls()
        elif token.isdigit():
            yield Num(int(token))
        elif token.isalpha():
            yield ID(token)
        else:
            raise ValueError(f"unrecognised token: {token}")
    yield EOF()


if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} \"math expression\"", file=sys.stderr)
    print(f"Example expression: (a() + 2) * 3 ^ 4 ^ 5", file=sys.stderr)
    exit(1)

tokens = list(tokenize(sys.argv[1]))
print("got the following tokens:", tokens)

lexer = Lexer(tokens)

print(Parser().parse())
