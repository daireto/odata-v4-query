from dataclasses import dataclass
from typing import Any, Literal, Protocol

from .definitions import OPERATOR_PRECEDENCE
from .errors import (
    CommaOrClosingParenthesisExpectedError,
    MissingClosingParenthesisError,
    OpeningParenthesisExpectedError,
    UnexpectedEndOfExpressionError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullIdentifierError,
    UnexpectedNullListError,
    UnexpectedNullLiteralError,
    UnexpectedNullNodeTypeError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnexpectedTokenError,
    UnknownNodeTypeError,
)
from .filter_tokenizer import (
    ODataFilterTokenizer,
    ODataFilterTokenizerProtocol,
    Token,
    TokenType,
)


@dataclass
class FilterNode:
    type_: Literal[
        'literal',
        'identifier',
        'operator',
        'function',
        'list',
        'value',
    ]
    value: Any | None = None
    left: 'FilterNode | None' = None
    right: 'FilterNode | None' = None
    arguments: list['FilterNode'] | None = None


class ODataFilterParserProtocol(Protocol):
    def parse(self, expr: str) -> FilterNode: ...

    def evaluate(self, node: FilterNode) -> str: ...


class ODataFilterParser:
    """Parser for OData V4 filter expressions."""

    __tokenizer: ODataFilterTokenizerProtocol
    """Tokenizer for the filter expression."""

    parse_null_identifier: bool
    """Whether to parse the null identifier."""

    def __init__(
        self,
        tokenizer: ODataFilterTokenizerProtocol | None = None,
        parse_null_identifier: bool = True,
    ) -> None:
        """Parser for OData V4 filter expressions.

        Parameters
        ----------
        tokenizer : ODataFilterTokenizerProtocol | None, optional
            Tokenizer, by default, it uses an instance of
            ``ODataFilterTokenizer``.
        parse_null_identifier : bool, optional
            Whether to parse the null identifier, by default True.

        """
        self.__tokenizer = tokenizer or ODataFilterTokenizer()
        self.parse_null_identifier = parse_null_identifier

    def set_tokenizer(self, tokenizer: ODataFilterTokenizerProtocol) -> None:
        """Set the tokenizer.

        Parameters
        ----------
        tokenizer : ODataFilterTokenizerProtocol
            Tokenizer.

        """
        self.__tokenizer = tokenizer  # pragma: no cover

    def parse(self, expr: str) -> FilterNode:
        """Parse a filter expression to an AST.

        Parameters
        ----------
        expr : str
            Filter expression to be parsed.

        Returns
        -------
        FilterNode
            AST representing the parsed filter expression.

        Examples
        --------
        >>> from odata_v4_query import ODataFilterParser
        >>> parser = ODataFilterParser()
        >>> ast = parser.parse("name eq 'John' and age gt 25")
        >>> ast
        FilterNode(type_='operator', value='and', left=FilterNode(...), right=FilterNode(...))

        """
        tokens = self.__tokenizer.tokenize(expr)
        if not tokens:
            return FilterNode(type_='value')

        return self._parse_expression(tokens)

    def evaluate(self, node: FilterNode) -> str:
        """Evaluate an AST to the original filter expression.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            Filter expression.

        Raises
        ------
        UnexpectedNullNodeTypeError
            If node type is None.
        UnknownNodeTypeError
            If node type is unknown.

        Examples
        --------
        >>> from odata_v4_query import ODataFilterParser
        >>> parser = ODataFilterParser()
        >>> ast = parser.parse("name eq 'John' and age gt 25")
        >>> parser.evaluate(ast)
        "name eq 'John' and age gt 25"

        """
        if not node.type_:
            raise UnexpectedNullNodeTypeError(repr(node))

        handlers = {
            'literal': self._evaluate_literal,
            'identifier': self._evaluate_identifier,
            'list': self._evaluate_list,
            'operator': self._evaluate_operator,
            'function': self._evaluate_function,
            'value': lambda n: repr(n.value),
        }

        handler = handlers.get(node.type_)
        if not handler:
            raise UnknownNodeTypeError(node.type_)

        return handler(node)

    def _parse_expression(
        self,
        tokens: list[Token],
        precedence: int = 0,
    ) -> FilterNode:
        """Parse an expression using precedence climbing.

        This method implements the precedence climbing algorithm
        to parse expressions with operators of different precedence
        levels. It handles binary operators and builds an Abstract
        Syntax Tree (AST) representing the expression structure.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.
        precedence : int, optional
            Minimum operator precedence level to consider,
            by default 0.

        Returns
        -------
        FilterNode
            AST node representing the parsed expression.

        Notes
        -----
        The precedence climbing algorithm works by:
        1. Parsing the leftmost expression first
        2. Looking ahead at the next operator
        3. If the operator has higher precedence than current level,
            recursively parse the right side
        4. Otherwise return the current expression

        """
        left = self._parse_primary(tokens)

        while tokens:
            token = tokens[0]
            if not isinstance(token, Token) or token.type_ != TokenType.OPERATOR:
                break

            op = token.value
            op_precedence = self._get_operator_precedence(op)  # type: ignore

            if op_precedence < precedence:
                break

            tokens.pop(0)  # consume operator
            right = self._parse_expression(tokens, op_precedence + 1)
            left = FilterNode(type_='operator', value=op, left=left, right=right)

        return left

    def _parse_primary(self, tokens: list[Token]) -> FilterNode:
        """Parse a primary expression.

        A primary expression is a literal, identifier, function call,
        or parenthesized expression. It is the smallest unit of an
        expression that can be evaluated.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.

        Returns
        -------
        FilterNode
            AST representing the parsed primary expression.

        Raises
        ------
        UnexpectedEndOfExpressionError
            If an unexpected end of expression is reached.
        OpeningParenthesisExpectedError
            If an opening parenthesis is expected, but not found.
        UnexpectedTokenError
            If an unexpected token is encountered.

        """
        if not tokens:
            raise UnexpectedEndOfExpressionError

        token = tokens.pop(0)

        if token.type_ == TokenType.LITERAL:
            return FilterNode(type_='literal', value=token.value)

        if token.type_ == TokenType.IDENTIFIER:
            if token.value == 'null' and self.parse_null_identifier:
                return FilterNode(type_='identifier', value=None)

            return FilterNode(type_='identifier', value=token.value)

        if token.type_ == TokenType.FUNCTION:
            func_name = token.value

            if not tokens or tokens[0].type_ != TokenType.LPAREN:
                raise OpeningParenthesisExpectedError(str(func_name))

            tokens.pop(0)  # consume '('

            args = self._parse_list_values(tokens)
            return FilterNode(type_='function', value=func_name, arguments=args)

        if token.type_ == TokenType.LPAREN:
            values = self._parse_list_values(tokens)
            return FilterNode(type_='list', arguments=values)

        if token.type_ == TokenType.OPERATOR and token.value == 'not':
            expr = self._parse_expression(tokens, self._get_operator_precedence('not'))
            return FilterNode(type_='operator', value='not', right=expr)

        raise UnexpectedTokenError(str(token.value), token.position)

    def _parse_list_values(self, tokens: list[Token]) -> list[FilterNode]:
        """Parse a list of values without consuming the opening parenthesis.

        This method is used to parse the arguments of a function call
        and the values of the ``in`` operator.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.

        Returns
        -------
        list[FilterNode]
            List of AST nodes representing the parsed values.

        Raises
        ------
        MissingClosingParenthesisError
            If closing parenthesis is missing.
        CommaOrClosingParenthesisExpectedError
            If no comma nor closing parenthesis is found.
        CommaOrClosingParenthesisExpectedError
            If token is neither a comma nor an closing parenthesis.

        """
        if not tokens:
            raise MissingClosingParenthesisError

        values = []

        # empty list
        if tokens[0].type_ == TokenType.RPAREN:
            tokens.pop(0)  # consume ')'
            return values

        while tokens:
            vnode = self._parse_expression(tokens)
            values.append(vnode)

            if not tokens:
                raise CommaOrClosingParenthesisExpectedError(
                    value=str(vnode.value),
                    expected_after=True,
                )

            # check for comma or closing parenthesis
            if tokens[0].type_ == TokenType.COMMA:
                tokens.pop(0)  # consume ','
            elif tokens[0].type_ == TokenType.RPAREN:
                tokens.pop(0)  # consume ')'
                break
            else:
                raise CommaOrClosingParenthesisExpectedError(value=str(tokens[0].value))

        return values

    def _get_operator_precedence(self, operator: str) -> int:
        """Return the precedence level of an operator.

        Parameters
        ----------
        operator : str
            Operator.

        Returns
        -------
        int
            Precedence level.

        """
        return OPERATOR_PRECEDENCE.get(operator, 0)

    def _evaluate_literal(self, node: FilterNode) -> str:
        """Evaluate a literal node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            Literal value.

        Raises
        ------
        UnexpectedNullLiteralError
            If node value is None.

        """
        if node.value is None:
            raise UnexpectedNullLiteralError(repr(node))

        # if it's numeric, don't add quotes
        if isinstance(node.value, (int, float)):
            return str(node.value)

        if isinstance(node.value, str):
            try:
                return str(float(node.value) if '.' in node.value else int(node.value))
            except ValueError:
                pass

        return f'{node.value!r}'

    def _evaluate_identifier(self, node: FilterNode) -> str:
        """Evaluate an identifier node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            Identifier value.

        Raises
        ------
        UnexpectedNullIdentifierError
            If node value is None.

        """
        if node.value is None:
            if self.parse_null_identifier:
                return 'null'

            raise UnexpectedNullIdentifierError(repr(node))

        return node.value

    def _evaluate_list(self, node: FilterNode, wrap_in_parentheses: bool = True) -> str:
        """Evaluate a list node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.
        wrap_in_parentheses : bool, optional
            Whether to wrap the list in parentheses, by default True.

        Returns
        -------
        str
            List value.

        Raises
        ------
        UnexpectedNullListError
            If node arguments is None.

        """
        if node.arguments is None:
            raise UnexpectedNullListError(repr(node))

        values = [self.evaluate(arg) for arg in node.arguments]

        if wrap_in_parentheses:
            return f'({", ".join(values)})'

        return ', '.join(values)

    def _evaluate_operator(self, node: FilterNode) -> str:
        """Evaluate an operator node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            Operator value.

        Raises
        ------
        UnexpectedNullOperatorError
            If node value is None.
        UnexpectedNullOperandError
            If node left or right is None.
        UnexpectedNullOperandError
            If node value is not ``not`` and node left
            or right is None.

        """
        if not node.value:
            raise UnexpectedNullOperatorError(repr(node))

        if node.value == 'not':
            if not node.right:
                raise UnexpectedNullOperandError(node.value)

            return f'not {self.evaluate(node.right)}'

        if not node.left or not node.right:
            raise UnexpectedNullOperandError(node.value)

        return f'{self.evaluate(node.left)} {node.value} {self.evaluate(node.right)}'

    def _evaluate_function(self, node: FilterNode) -> str:
        """Evaluate a function node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            Function value.

        Raises
        ------
        UnexpectedNullFunctionNameError
            If node value is None.

        """
        if not node.value:
            raise UnexpectedNullFunctionNameError(repr(node))

        args = self._evaluate_list(node, wrap_in_parentheses=False)
        return f'{node.value}({args})'
