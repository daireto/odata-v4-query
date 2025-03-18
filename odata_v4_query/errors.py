class ODataParserError(Exception):
    """Base class for all OData parser errors."""


class EvaluateError(ODataParserError, ValueError):
    """Evaluation error."""

    def __init__(self, message: str) -> None:
        """Evaluation error.

        Parameters
        ----------
        message : str
            Error message.
        """
        super().__init__(message)


class InvalidNumberError(ODataParserError, ValueError):
    """Invalid number error."""

    def __init__(self, value: str, position: int) -> None:
        """Invalid number error.

        Parameters
        ----------
        value : str
            Value.
        position : int
            Start position.
        """
        super().__init__(
            f'invalid number at position {position}, got {value!r}'
        )


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


class NoRootClassFound(ODataParserError, ValueError):
    """No root class found error."""

    def __init__(self, query: str, option_name: str) -> None:
        """No root class found error.

        Parameters
        ----------
        query : str
            Query.
        """
        super().__init__(f'could not find root class of query: {query!r}')
        self.add_note(f'cannot apply {option_name} option')


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
            f'unexpected character {char!r} at position {position}'
        )


class UnexpectedNullOperand(ODataParserError, ValueError):
    """Unexpected null operand error."""

    def __init__(self, operator: str) -> None:
        """Unexpected null operand error.

        Parameters
        ----------
        operator : str
            Operator.
        """
        super().__init__(f'unexpected null operand for operator {operator!r}')


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
