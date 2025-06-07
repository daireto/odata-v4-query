class ODataParserError(Exception):
    """Base class for all OData parser errors."""


class InvalidOrderDirectionError(ODataParserError, ValueError):
    """Invalid order direction error."""

    def __init__(self, direction: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        direction : str
            Direction.

        """
        super().__init__(f'invalid order direction {direction!r}')


class InvalidNumberError(ODataParserError, ValueError):
    """Invalid number error."""

    def __init__(self, value: str, position: int) -> None:
        """Initialize the error.

        Parameters
        ----------
        value : str
            Value.
        position : int
            Start position.

        """
        super().__init__(
            f'invalid number at position {position}, got {value!r}',
        )


class OpeningParenthesisExpectedError(ODataParserError, ValueError):
    """Opening parenthesis expected error."""

    def __init__(self, func_name: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        func_name : str
            Function name.

        """
        super().__init__(f"expected '(' after {func_name!r} function name")


class CommaOrClosingParenthesisExpectedError(ODataParserError, ValueError):
    """Comma or closing parenthesis expected error."""

    def __init__(self, value: str, expected_after: bool = False) -> None:
        """Initialize the error.

        Parameters
        ----------
        value : str
            Value.
        expected_after : bool, optional
            Whether the comma or closing parenthesis is expected
            after the value, by default False.

        """
        value = f' after {value!r}' if expected_after else f', got {value!r}'
        super().__init__(f"expected ',' or ')'{value}")


class MissingClosingParenthesisError(ODataParserError, ValueError):
    """Missing closing parenthesis error."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__('missing closing parenthesis')


class NoNumericValueError(ODataParserError, ValueError):
    """No numeric value error."""

    def __init__(self, value: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        value : str
            Value.

        """
        super().__init__(f'expected a numeric value, got {value!r}')


class NoPositiveError(ODataParserError, ValueError):
    """No positive integer value error."""

    def __init__(self, param: str, value: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        param : str
            Parameter.
        value : str
            Value.

        """
        super().__init__(f'expected {param} to be a positive integer, got {value!r}')


class NoRootClassError(ODataParserError, ValueError):
    """No root class found error."""

    def __init__(self, query: str, option_name: str | None = None) -> None:
        """Initialize the error.

        Parameters
        ----------
        query : str
            Query.
        option_name : str | None, optional
            Option name, by default None.

        """
        super().__init__(f'could not find root class of query {query!r}')
        if option_name:
            self.add_note(f'cannot apply {option_name} option')


class TokenizeError(ODataParserError, ValueError):
    """Tokenizer error."""

    def __init__(self, char: str, position: int) -> None:
        """Initialize the error.

        Parameters
        ----------
        char : str
            Character.
        position : int
            Character position.

        """
        super().__init__(f'unexpected character {char!r} at position {position}')


class TwoArgumentsExpectedError(ODataParserError, ValueError):
    """Two arguments expected error."""

    def __init__(self, function_name: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        function_name : str
            Function name.

        """
        super().__init__(f'expected 2 arguments for function {function_name!r}')


class UnexpectedEmptyArgumentsError(ODataParserError, ValueError):
    """Unexpected empty arguments error."""

    def __init__(self, function_name: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        function_name : str
            Function name.

        """
        super().__init__(f'unexpected empty arguments for function {function_name!r}')


class UnexpectedEndOfExpressionError(ODataParserError, ValueError):
    """Unexpected end of expression error."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__('unexpected end of expression')


class UnexpectedNullFiltersError(ODataParserError, ValueError):
    """Unexpected null filters error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null filters in {node_repr!r}')


class UnexpectedNullFunctionNameError(ODataParserError, ValueError):
    """Unexpected null function name error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null function name in {node_repr!r}')


class UnexpectedNullIdentifierError(ODataParserError, ValueError):
    """Unexpected null identifier error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null identifier in {node_repr!r}')


class UnexpectedNullListError(ODataParserError, ValueError):
    """Unexpected null list error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null list in {node_repr!r}')


class UnexpectedNullLiteralError(ODataParserError, ValueError):
    """Unexpected null literal error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null literal in {node_repr!r}')


class UnexpectedNullNodeTypeError(ODataParserError, ValueError):
    """Unexpected null node type error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null node type in {node_repr!r}')


class UnexpectedNullOperandError(ODataParserError, ValueError):
    """Unexpected null operand error."""

    def __init__(self, operator_or_function: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        operator_or_function : str
            Operator or function.

        """
        super().__init__(
            f'unexpected null operand for {operator_or_function!r}',
        )


class UnexpectedNullOperatorError(ODataParserError, ValueError):
    """Unexpected null operator error."""

    def __init__(self, node_repr: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_repr : str
            Node representation.

        """
        super().__init__(f'unexpected null operator in {node_repr!r}')


class UnexpectedTokenError(ODataParserError, ValueError):
    """Unexpected token error."""

    def __init__(self, token: str, position: int) -> None:
        """Initialize the error.

        Parameters
        ----------
        token : str
            Token.
        position : int
            Token position.

        """
        super().__init__(f'unexpected token {token!r} at position {position}')


class UnknownFunctionError(ODataParserError, ValueError):
    """Unknown function error."""

    def __init__(self, function_name: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        function_name : str
            Function name.

        """
        super().__init__(f'unknown function {function_name!r}')


class UnknownNodeTypeError(ODataParserError, ValueError):
    """Unknown node type error."""

    def __init__(self, node_type: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        node_type : str
            Node type.

        """
        super().__init__(f'unknown node type {node_type!r}')


class UnknownOperatorError(ODataParserError, ValueError):
    """Unknown operator error."""

    def __init__(self, operator: str) -> None:
        """Initialize the error.

        Parameters
        ----------
        operator : str
            Operator.

        """
        super().__init__(f'unknown operator {operator!r}')


class UnsupportedFormatError(ODataParserError, ValueError):
    """Initialize the error."""

    def __init__(self, fmt: str) -> None:
        """Unsupported format error.

        Parameters
        ----------
        fmt : str
            Format.

        """
        super().__init__(f'unsupported format {fmt!r}')
