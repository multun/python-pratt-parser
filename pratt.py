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
    def __init__(self, func, args):
        self.func = func
        self.args = args

    def __repr__(self):
        args_repr = ', '.join(repr(arg) for arg in self.args)
        return f"{operator_name(self.func)}({args_repr})"


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
    pass


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


tokens = [LParen(), ID("a"), LParen(), RParen(), Plus(), Num(2), RParen(),
          Mult(), Num(3), Exp(), Num(4), Exp(), Num(5), EOF()]
print(tokens)

# tokens = [ID("a"), Plus(), Num(2), EOF()]
# print(tokens)
lexer = Lexer(tokens)

print(Parser().parse())
