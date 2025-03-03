from dataclasses import dataclass
from typing import Literal

from .errors import ParseError
from .filter_tokenizer import ODataFilterTokenizer, Token, TokenType


@dataclass
class FilterNode:
    type_: Literal['literal', 'identifier', 'operator', 'function', 'list']
    value: str | None = None
    left: 'FilterNode | None' = None
    right: 'FilterNode | None' = None
    arguments: list['FilterNode'] | None = None


class ODataFilterParser:
    """Parser for OData V4 filter expressions."""

    position: int
    """Current position in the filter expression."""

    tokens: list[Token]
    """Tokens extracted from the filter expression."""

    tokenizer: ODataFilterTokenizer
    """Tokenizer for the filter expression."""

    def __init__(self):
        self.position = 0
        self.tokens: list[Token] = []
        self.tokenizer = ODataFilterTokenizer()

    def parse(self, filter_expression: str) -> FilterNode:
        """Parses a filter expression and returns an AST.

        Parameters
        ----------
        filter_expression : str
            Filter expression to be parsed.

        Returns
        -------
        FilterNode
            AST representing the parsed filter expression.
        """
        tokens = self.tokenizer.tokenize(filter_expression)
        return self._parse_expression(tokens)

    def evaluate(self, node: FilterNode) -> str:
        """Converts the AST back to a filter expression string
        (for debugging/validation).
        """
        if node.type_ == 'literal':
            if not node.value:
                raise ParseError('unexpected null literal')

            # if it's numeric, don't add quotes
            if node.value.isdigit() or (
                node.value.replace('.', '', 1).isdigit()
                and node.value.count('.') <= 1
            ):
                return node.value

            return f"'{node.value}'"

        elif node.type_ == 'identifier':
            if not node.value:
                raise ParseError('unexpected null identifier')

            return node.value

        elif node.type_ == 'list':
            if not node.arguments:
                raise ParseError('unexpected empty list')

            values = [self.evaluate(arg) for arg in node.arguments]
            return f"({', '.join(values)})"

        elif node.type_ == 'operator':
            if not node.value:
                raise ParseError('unexpected null operator')

            if not node.left or not node.right:
                raise ParseError(
                    f'unexpected null operand for operator {node.value!r}'
                )

            if node.value == 'not':
                return f'not {self.evaluate(node.right)}'

            return (
                f'({self.evaluate(node.left)} {node.value} '
                f'{self.evaluate(node.right)})'
            )

        elif node.type_ == 'function':
            if not node.value:
                raise ParseError('unexpected null function name')

            if not node.arguments:
                raise ParseError(
                    'unexpected empty function arguments for '
                    f'function {node.value!r}'
                )

            args = [self.evaluate(arg) for arg in node.arguments]
            return f"{node.value}({', '.join(args)})"

        raise ParseError(f"Unknown node type: {node.type_}")

    def _parse_expression(
        self, tokens: list[Token], precedence: int = 0
    ) -> FilterNode:
        """Parses an expression using precedence climbing.

        Parameters
        ----------
        tokens : list[Token]
            List of tokens extracted from the filter expression.
        precedence : int, optional
            Operator precedence, by default 0.

        Returns
        -------
        FilterNode
            AST representing the parsed expression.
        """
        left = self._parse_primary(tokens)

        while tokens and isinstance(tokens[0], Token):
            if tokens[0].type_ == TokenType.OPERATOR:
                op = tokens[0].value
                op_precedence = self._get_operator_precedence(op)

                if op_precedence < precedence:
                    break

                tokens.pop(0)  # consume operator
                right = self._parse_expression(tokens, op_precedence + 1)

                left = FilterNode(
                    type_='operator', value=op, left=left, right=right
                )
            else:
                break

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
        precedence = {
            'or': 1,
            'and': 2,
            'eq': 3,
            'ne': 3,
            'lt': 4,
            'gt': 4,
            'le': 4,
            'ge': 4,
            'in': 5,
            'has': 5,
            'not': 6,
        }
        return precedence.get(operator, 0)
