class ODataParserError(Exception):
    """Base class for all OData parser errors."""


class ParseError(ODataParserError, ValueError):
    """Parser error."""

    def __init__(self, message: str) -> None:
        """Parser error.

        Parameters
        ----------
        message : str
            Error message.
        """
        super().__init__(message)


class NoPositiveIntegerValue(ODataParserError, ValueError):
    """No positive integer value error."""

    def __init__(self, param: str, value: str) -> None:
        """No positive integer value error.

        Parameters
        ----------
        param : str
            Parameter.
        value : str
            Value.
        """
        super().__init__(
            f'expected {param} to be a positive integer, got {value!r}'
        )


class TokenizeError(ODataParserError, ValueError):
    """Tokenizer error."""

    def __init__(self, char: str, position: int) -> None:
        """Tokenizer error.

        Parameters
        ----------
        char : str
            Character.
        position : int
            Character position.
        """
        super().__init__(
            f'unexpected character {char!r} at position {self.position}'
        )
        self.char = char
        self.position = position


class UnsupportedFormat(ODataParserError, ValueError):
    """Unsupported format error."""

    def __init__(self, fmt: str) -> None:
        """Unsupported format error.

        Parameters
        ----------
        fmt : str
            Format.
        """
        super().__init__(
            f'unsupported format: {fmt!r}. Supported formats: '
            'json, xml, csv, tsv'
        )
