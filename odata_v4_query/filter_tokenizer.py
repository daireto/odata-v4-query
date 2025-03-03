from dataclasses import dataclass
from enum import Enum

from .errors import TokenizeError


class TokenType(Enum):
    OPERATOR = 'OPERATOR'
    FUNCTION = 'FUNCTION'
    IDENTIFIER = 'IDENTIFIER'
    LITERAL = 'LITERAL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    COMMA = 'COMMA'


@dataclass
class Token:
    type_: TokenType
    value: str
    position: int


class ODataFilterTokenizer:
    """Tokenizer for OData V4 filter expressions."""

    operators = {
        'eq': 2,  # equals
        'ne': 2,  # not equals
        'gt': 2,  # greater than
        'ge': 2,  # greater than or equals
        'lt': 2,  # less than
        'le': 2,  # less than or equals
        'and': 2,  # logical and
        'or': 2,  # logical or
        'not': 1,  # logical not
        'in': 2,  # in operator
        'has': 2,  # has operator
    }
    """Supported operators."""

    functions = {
        'startswith': 2,
        'endswith': 2,
        'contains': 2,
    }
    """Supported functions."""

    def tokenize(self, expression: str) -> list[Token]:
        """Converts filter expression string into tokens.

        Parameters
        ----------
        expression : str
            Filter expression to be tokenized.

        Returns
        -------
        list[Token]
            List of tokens extracted from the filter expression.

        Raises
        ------
        TokenizeError
            If the filter expression is invalid.

        Examples
        --------
        >>> tokenizer = ODataFilterTokenizer()
        >>> tokens = tokenizer.tokenize("name eq 'John' and age gt 25")
        >>> for token in tokens:
        ...     print(token.type, token.value)
        Token(type_=<TokenType.IDENTIFIER: 'IDENTIFIER'>, value='name', position=0)
        Token(type_=<TokenType.OPERATOR: 'OPERATOR'>, value='eq', position=5)
        Token(type_=<TokenType.LITERAL: 'LITERAL'>, value='John', position=8)
        Token(type_=<TokenType.OPERATOR: 'OPERATOR'>, value='and', position=15)
        Token(type_=<TokenType.IDENTIFIER: 'IDENTIFIER'>, value='age', position=19)
        Token(type_=<TokenType.OPERATOR: 'OPERATOR'>, value='gt', position=23)
        Token(type_=<TokenType.LITERAL: 'LITERAL'>, value='25', position=26)
        """
        self.position = 0
        self.tokens = []

        while self.position < len(expression):
            char = expression[self.position]

            # skip whitespace
            if char.isspace():
                self.position += 1
                continue

            # handle parentheses
            if char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.position))
                self.position += 1
                continue
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.position))
                self.position += 1
                continue

            # handle comma
            if char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.position))
                self.position += 1
                continue

            # handle string literals
            if char == "'":
                value, pos = self._extract_string_literal(expression)
                self.tokens.append(Token(TokenType.LITERAL, value, pos))
                continue

            # handle numbers
            if char.isdigit():
                value, pos = self._extract_number(expression)
                self.tokens.append(Token(TokenType.LITERAL, value, pos))
                continue

            # handle identifiers, operators, and functions
            if char.isalpha():
                value, pos = self._extract_identifier(expression)

                if value.lower() in self.operators:
                    self.tokens.append(
                        Token(TokenType.OPERATOR, value.lower(), pos)
                    )
                elif value.lower() in self.functions:
                    self.tokens.append(
                        Token(TokenType.FUNCTION, value.lower(), pos)
                    )
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, value, pos))
                continue

            raise TokenizeError(char, self.position)

        return self.tokens

    def _extract_string_literal(self, expression: str) -> tuple[str, int]:
        """Extracts a string literal from the expression.

        Parameters
        ----------
        expression : str
            Expression to extract the string literal from.

        Returns
        -------
        tuple[str, int]
            A tuple containing the string literal and the position of
            the first character of the string literal.
        """
        start_pos = self.position
        self.position += 1  # skip opening quote
        value = ''

        while self.position < len(expression):
            char = expression[self.position]
            if char == "'":
                if (
                    self.position + 1 < len(expression)
                    and expression[self.position + 1] == "'"
                ):
                    # handle escaped single quote
                    value += "'"
                    self.position += 2
                else:
                    # end of string
                    self.position += 1
                    break
            else:
                value += char
                self.position += 1

        return value, start_pos

    def _extract_number(self, expression: str) -> tuple[str, int]:
        """Extracts a number from the expression.

        Parameters
        ----------
        expression : str
            Expression to extract the number from.

        Returns
        -------
        tuple[str, int]
            A tuple containing the number and the position of
            the first character of the number.
        """
        start_pos = self.position
        value = ''

        while self.position < len(expression):
            char = expression[self.position]
            if char.isdigit() or char == '.':
                value += char
                self.position += 1
            else:
                break

        return value, start_pos

    def _extract_identifier(self, expression: str) -> tuple[str, int]:
        """Extracts an identifier from the expression.

        Parameters
        ----------
        expression : str
            Expression to extract the identifier from.

        Returns
        -------
        tuple[str, int]
            A tuple containing the identifier and the position of
            the first character of the identifier.
        """
        start_pos = self.position
        value = ''

        while self.position < len(expression):
            char = expression[self.position]
            if char.isalnum() or char == '_' or char == '/':
                value += char
                self.position += 1
            else:
                break

        return value, start_pos
