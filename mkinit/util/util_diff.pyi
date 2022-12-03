from _typeshed import Incomplete

NO_COLOR: Incomplete


def difftext(text1: str,
             text2: str,
             context_lines: int = 0,
             ignore_whitespace: bool = False,
             colored: bool = False) -> str:
    ...


def highlight_code(text: str, lexer_name: str = 'python', **kwargs) -> str:
    ...
