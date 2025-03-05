from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Protocol

from .errors import ParseError
from .filter_tokenizer import (
    ODataFilterTokenizer,
    ODataFilterTokenizerProtocol,
    Token,
    TokenType,
)

OPERATOR_PRECEDENCE = {
    'not': 3,
    'and': 2,
    'or': 1,
    'eq': 2,
    'ne': 2,
    'gt': 2,
    'ge': 2,
    'lt': 2,
    'le': 2,
    'in': 2,
    'has': 2,
}
"""Operator precedence."""


@dataclass
class FilterNode:
    type_: Literal['literal', 'identifier', 'operator', 'function', 'list']
    value: str | None = None
    left: 'FilterNode | None' = None
    right: 'FilterNode | None' = None
    arguments: list['FilterNode'] | None = None


class ODataFilterParserProtocol(Protocol):

    def parse(self, expr: str) -> FilterNode:
        """Parses a filter expression and returns an AST.

        Parameters
        ----------
        expr : str
            Filter expression to be parsed.

        Returns
        -------
        FilterNode
            AST representing the parsed filter expression.
        """
        ...


class ODataFilterParser:
    """Parser for OData V4 filter expressions."""

    __tokenizer: ODataFilterTokenizerProtocol
    """Tokenizer for the filter expression."""

    def __init__(self, tokenizer: ODataFilterTokenizerProtocol | None = None):
        """Parser for OData V4 filter expressions.

        Parameters
        ----------
        tokenizer : ODataFilterTokenizerProtocol | None, optional
            Tokenizer, by default None.
        """
        self.__tokenizer = tokenizer or ODataFilterTokenizer()

    def set_tokenizer(self, tokenizer: ODataFilterTokenizerProtocol) -> None:
        """Sets the tokenizer.

        Parameters
        ----------
        tokenizer : ODataFilterTokenizerProtocol
            Tokenizer.
        """
        self.__tokenizer = tokenizer

    @lru_cache(maxsize=128)
    def parse(self, expr: str) -> FilterNode:
        """Parses a filter expression and returns an AST.

        Results are cached for better performance on
        repeated expressions.

        Parameters
        ----------
        expr : str
            Filter expression to be parsed.

        Returns
        -------
        FilterNode
            AST representing the parsed filter expression.
        """
        tokens = self.__tokenizer.tokenize(expr)
        return self._parse_expression(tokens)

    def evaluate(self, node: FilterNode) -> str:
        """Evaluates an AST and returns the corresponding expression.

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
        ParseError
            If node type is None.
        ParseError
            If node type is unknown.
        """
        if not node.type_:
            raise ParseError('node type cannot be None')

        handlers = {
            'literal': self._evaluate_literal,
            'identifier': self._evaluate_identifier,
            'list': self._evaluate_list,
            'operator': self._evaluate_operator,
            'function': self._evaluate_function,
        }

        handler = handlers.get(node.type_)
        if not handler:
            raise ParseError(f'unknown node type: {node.type_!r}')

        return handler(node)

    def _evaluate_literal(self, node: FilterNode) -> str:
        """Evaluates a literal node.

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
        ParseError
            If node value is None.
        """
        if not node.value:
            raise ParseError('unexpected null literal')

        # if it's numeric, don't add quotes
        if node.value.isdigit() or (
            node.value.replace('.', '', 1).isdigit()
            and node.value.count('.') <= 1
        ):
            return node.value

        return f"{node.value!r}"

    def _evaluate_identifier(self, node: FilterNode) -> str:
        """Evaluates an identifier node.

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
        ParseError
            If node value is None.
        """
        if not node.value:
            raise ParseError('unexpected null identifier')
        return node.value

    def _evaluate_list(self, node: FilterNode) -> str:
        """Evaluates a list node.

        Parameters
        ----------
        node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        str
            List value.

        Raises
        ------
        ParseError
            If node arguments is None.
        """
        if not node.arguments:
            raise ParseError('unexpected empty list')
        values = [self.evaluate(arg) for arg in node.arguments]
        return f"({', '.join(values)})"

    def _evaluate_operator(self, node: FilterNode) -> str:
        if not node.value:
            raise ParseError('unexpected null operator')

        if node.value == 'not':
            if not node.right:
                raise ParseError('unexpected null operand for operator "not"')
            return f'not {self.evaluate(node.right)}'

        if not node.left or not node.right:
            raise ParseError(
                f'unexpected null operand for operator {node.value!r}'
            )

        return f'({self.evaluate(node.left)} {node.value} {self.evaluate(node.right)})'

    def _evaluate_function(self, node: FilterNode) -> str:
        if not node.value:
            raise ParseError('unexpected null function name')
        if not node.arguments:
            raise ParseError(
                f'unexpected empty function arguments for function {node.value!r}'
            )

        args = [self.evaluate(arg) for arg in node.arguments]
        return f"{node.value}({', '.join(args)})"

    def _parse_expression(
        self, tokens: list[Token], precedence: int = 0
    ) -> FilterNode:
        """Parses an expression using precedence climbing.

        This method implements the precedence climbing algorithm to parse
        expressions with operators of different precedence levels. It handles
        binary operators and builds an Abstract Syntax Tree (AST) representing
        the expression structure.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.
        precedence : int, optional
            Minimum operator precedence level to consider, by default 0.

        Returns
        -------
        FilterNode
            AST node representing the parsed expression.

        Raises
        ------
        ParseError
            If an invalid token is encountered or if the expression structure
            is invalid.

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
            if (
                not isinstance(token, Token)
                or token.type_ != TokenType.OPERATOR
            ):
                break

            op = token.value
            op_precedence = self._get_operator_precedence(op)

            if op_precedence < precedence:
                break

            tokens.pop(0)  # consume operator
            right = self._parse_expression(tokens, op_precedence + 1)
            left = FilterNode(
                type_='operator', value=op, left=left, right=right
            )

        return left

    def _parse_primary(self, tokens: list[Token]) -> FilterNode:
        """Parses a primary expression (literal, identifier,
        function call, or parenthesized expression).

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
        ParseError
            If an unexpected end of expression is reached.
        ParseError
            If an unexpected end of value list is reached.
        ParseError
            If token is neither a comma nor an closing parenthesis
            in the ``in`` operator case.
        ParseError
            If closing parenthesis is missing.
        ParseError
            If an unexpected token is encountered.
        """
        if not tokens:
            raise ParseError('unexpected end of expression')

        token = tokens.pop(0)

        if token.type_ == TokenType.LITERAL:
            return FilterNode(type_='literal', value=token.value)

        elif token.type_ == TokenType.IDENTIFIER:
            identifier_node = FilterNode(type_='identifier', value=token.value)

            # check if this identifier is followed by an
            # 'in' operator with a list
            if (
                tokens
                and tokens[0].type_ == TokenType.OPERATOR
                and tokens[0].value == 'in'
            ):
                tokens.pop(0)  # consume 'in'

                # handle list of values for 'in' operator
                if tokens and tokens[0].type_ == TokenType.LPAREN:
                    tokens.pop(0)  # consume '('

                    values = []
                    while tokens:
                        if tokens[0].type_ == TokenType.RPAREN:
                            tokens.pop(0)  # consume ')'
                            break

                        value_node = self._parse_expression(tokens)
                        values.append(value_node)

                        if not tokens:
                            raise ParseError(
                                'unexpected end of value list after '
                                f'{value_node.value!r}'
                            )

                        # check for comma or closing parenthesis
                        if tokens[0].type_ == TokenType.COMMA:
                            tokens.pop(0)  # consume ','
                        elif tokens[0].type_ != TokenType.RPAREN:
                            raise ParseError(
                                f"expected ',' or ')', got {tokens[0].value!r}"
                            )

                    # create 'in' operator node
                    return FilterNode(
                        type_='operator',
                        value='in',
                        left=identifier_node,
                        right=FilterNode(type_='list', arguments=values),
                    )

            return identifier_node

        elif token.type_ == TokenType.FUNCTION:
            func_name = token.value
            args = self._parse_function_arguments(tokens)
            return FilterNode(
                type_='function', value=func_name, arguments=args
            )

        elif token.type_ == TokenType.LPAREN:
            expr = self._parse_expression(tokens)
            if not tokens or tokens[0].type_ != TokenType.RPAREN:
                raise ParseError(
                    f'missing closing parenthesis after {expr.value!r}'
                )

            tokens.pop(0)  # consume ')'
            return expr

        elif token.type_ == TokenType.OPERATOR and token.value == 'not':
            expr = self._parse_expression(
                tokens, self._get_operator_precedence('not')
            )
            return FilterNode(type_='operator', value='not', right=expr)

        raise ParseError(
            f'unexpected token {token.value!r} at position {token.position}'
        )

    def _parse_function_arguments(
        self, tokens: list[Token]
    ) -> list[FilterNode]:
        """Parses function arguments.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.

        Returns
        -------
        list[FilterNode]
            List of function arguments.

        Raises
        ------
        ParseError
            If token after function name is not an opening parenthesis.
        ParseError
            If an unexpected end of value list is reached.
        ParseError
            If token is neither a comma nor an closing parenthesis.
        """
        args = []

        if not tokens or tokens[0].type_ != TokenType.LPAREN:
            raise ParseError("expected '(' after function name")

        tokens.pop(0)  # consume '('

        # handle case of no arguments
        if tokens and tokens[0].type_ == TokenType.RPAREN:
            tokens.pop(0)  # consume ')'
            return args

        while tokens:
            arg = self._parse_expression(tokens)
            args.append(arg)

            if not tokens:
                raise ParseError(
                    f'unexpected end of value list after {arg.value!r}'
                )

            # check for comma or closing parenthesis
            if tokens[0].type_ == TokenType.COMMA:
                tokens.pop(0)  # consume ','
            elif tokens[0].type_ == TokenType.RPAREN:
                tokens.pop(0)  # consume ')'
                break
            else:
                raise ParseError(
                    f"expected ',' or ')', got {tokens[0].value!r}"
                )

        return args

    def _get_operator_precedence(self, operator: str) -> int:
        """Returns the precedence level of an operator.

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
