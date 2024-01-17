from _typeshed import Incomplete
from typing import NamedTuple

__credits__: str
cookie_re: Incomplete
blank_re: Incomplete


class TokenInfo(
        NamedTuple('TokenInfo', [('type', Incomplete), ('string', Incomplete),
                                 ('start', Incomplete), ('end', Incomplete),
                                 ('line', Incomplete)])):

    @property
    def exact_type(self):
        ...


def group(*choices):
    ...


def any(*choices):
    ...


def maybe(*choices):
    ...


Whitespace: str
Comment: str
Ignore: Incomplete
Name: str
Hexnumber: str
Binnumber: str
Octnumber: str
Decnumber: str
Intnumber: Incomplete
Exponent: str
Pointfloat: Incomplete
Expfloat: Incomplete
Floatnumber: Incomplete
Imagnumber: Incomplete
Number: Incomplete
StringPrefix: Incomplete
Single: str
Double: str
Single3: str
Double3: str
Triple: Incomplete
String: Incomplete
Special: Incomplete
Funny: Incomplete
PlainToken: Incomplete
Token: Incomplete
ContStr: Incomplete
PseudoExtras: Incomplete
PseudoToken: Incomplete
endpats: Incomplete
single_quoted: Incomplete
triple_quoted: Incomplete
tabsize: int


class TokenError(Exception):
    ...


class StopTokenizing(Exception):
    ...


class Untokenizer:
    tokens: Incomplete
    prev_row: int
    prev_col: int
    encoding: Incomplete

    def __init__(self) -> None:
        ...

    def add_whitespace(self, start) -> None:
        ...

    def untokenize(self, iterable):
        ...

    def compat(self, token, iterable) -> None:
        ...


def untokenize(iterable):
    ...


def detect_encoding(readline):
    ...


def open(filename):
    ...


def tokenize(readline):
    ...


def generate_tokens(readline):
    ...


def main() -> None:
    ...
