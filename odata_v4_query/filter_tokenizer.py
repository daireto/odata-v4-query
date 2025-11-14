from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .definitions import FUNCTION_ARITY, OPERATOR_ARITY
from .errors import InvalidNumberError, TokenizeError


class TokenType(str, Enum):
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
    value: str | int | float
    position: int
    args_count: int | None = None


class ODataFilterTokenizerProtocol(Protocol):
    def tokenize(self, expr: str) -> list[Token]: ...


class ODataFilterTokenizer:
    """Tokenizer for OData V4 filter expressions."""

    __position: int
    __tokens: list[Token]

    def tokenize(self, expr: str) -> list[Token]:
        """Convert filter expression string into tokens.

        Parameters
        ----------
        expr : str
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
        >>> from odata_v4_query import ODataFilterTokenizer
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
        self.__position = 0
        self.__tokens = []
        expr_len = len(expr)

        char_handlers = {
            '(': lambda: self.__tokens.append(
                Token(TokenType.LPAREN, '(', self.__position),
            ),
            ')': lambda: self.__tokens.append(
                Token(TokenType.RPAREN, ')', self.__position),
            ),
            ',': lambda: self.__tokens.append(
                Token(TokenType.COMMA, ',', self.__position),
            ),
            "'": lambda: self._handle_string_literal(expr),
            '"': lambda: self._handle_string_literal(expr),
        }

        while self.__position < expr_len:
            char = expr[self.__position]

            # skip whitespace
            if char.isspace():
                self.__position += 1
                continue

            # Handle special characters using dispatch dictionary
            handler = char_handlers.get(char)
            if handler:
                handler()
                self.__position += 1
                continue

            # handle numbers (including negative numbers)
            if char.isdigit() or (char == '-' and self.__position + 1 < expr_len and expr[self.__position + 1].isdigit()):
                value, pos = self._extract_number(expr)
                self.__tokens.append(Token(TokenType.LITERAL, value, pos))
                continue

            # handle identifiers, operators, and functions
            if char.isalpha():
                value, pos = self._extract_identifier(expr)
                lowercased_value = value.lower()

                if lowercased_value in OPERATOR_ARITY:
                    self.__tokens.append(
                        Token(
                            TokenType.OPERATOR,
                            lowercased_value,
                            pos,
                            OPERATOR_ARITY[lowercased_value],
                        ),
                    )
                elif lowercased_value in FUNCTION_ARITY:
                    self.__tokens.append(
                        Token(
                            TokenType.FUNCTION,
                            lowercased_value,
                            pos,
                            FUNCTION_ARITY[lowercased_value],
                        ),
                    )
                else:
                    self.__tokens.append(
                        Token(TokenType.IDENTIFIER, value, pos),
                    )
                continue

            raise TokenizeError(char, self.__position)

        return self.__tokens

    def _handle_string_literal(self, expr: str) -> None:
        """Handle string literals.

        Parameters
        ----------
        expr : str
            Expression to extract the string literal from.

        """
        value, pos = self._extract_string_literal(expr)
        self.__tokens.append(Token(TokenType.LITERAL, value, pos))

    def _extract_string_literal(self, expr: str) -> tuple[str, int]:
        """Extract a string literal from the expression.

        Parameters
        ----------
        expr : str
            Expression to extract the string literal from.

        Returns
        -------
        tuple[str, int]
            A tuple containing the string literal and the position of
            the first character of the string literal.

        """
        start_pos = self.__position
        expr_len = len(expr)
        end_pos = start_pos + 1  # skip opening quote
        chars = []

        while end_pos < expr_len:
            char = expr[end_pos]

            # handle escaped characters
            if char == '\\':
                if end_pos + 1 >= expr_len:
                    break

                chars.append(expr[end_pos + 1])
                end_pos += 2
                continue

            # append non-quote characters
            if char not in {"'", '"'}:
                chars.append(char)
                end_pos += 1
                continue

            # end of string literal
            break

        self.__position = end_pos
        return ''.join(chars), start_pos

    def _extract_number(self, expr: str) -> tuple[int | float, int]:
        """Extract a number from the expression.

        Parameters
        ----------
        expr : str
            Expression to extract the number from.

        Returns
        -------
        tuple[int | float, int]
            A tuple containing the number and the position of
            the first character of the number.

        Raises
        ------
        InvalidNumberError
            If the number is invalid.

        """
        start_pos = self.__position
        expr_len = len(expr)
        end_pos = start_pos
        has_decimal = False

        # Handle negative sign
        if end_pos < expr_len and expr[end_pos] == '-':
            end_pos += 1

        while end_pos < expr_len:
            char = expr[end_pos]
            if char.isdigit():
                end_pos += 1
            elif char == '.':
                if has_decimal:
                    raise InvalidNumberError(
                        expr[start_pos:end_pos],
                        start_pos,
                    )

                has_decimal = True
                end_pos += 1
            elif char.isalpha():
                raise InvalidNumberError(expr[start_pos:end_pos], start_pos)
            else:
                break

        self.__position = end_pos

        value = expr[start_pos:end_pos]
        number = float(value) if '.' in value else int(value)
        return number, start_pos

    def _extract_identifier(self, expr: str) -> tuple[str, int]:
        """Extract an identifier from the expression.

        Parameters
        ----------
        expr : str
            Expression to extract the identifier from.

        Returns
        -------
        tuple[str, int]
            A tuple containing the identifier and the position of
            the first character of the identifier.

        """
        start_pos = self.__position
        expr_len = len(expr)
        end_pos = start_pos

        while end_pos < expr_len:
            char = expr[end_pos]
            if not (char.isalnum() or char in '_/'):
                break
            end_pos += 1

        self.__position = end_pos
        return expr[start_pos:end_pos], start_pos
