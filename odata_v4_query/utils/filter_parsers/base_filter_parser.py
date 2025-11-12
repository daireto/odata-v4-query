"""Base class for filter node parsers."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from odata_v4_query.definitions import (
    AND,
    COMPARISON_OPERATORS,
    CONTAINS,
    ENDSWITH,
    EQ,
    FUNCTION_ARITY,
    HAS,
    IN,
    LOGICAL_OPERATORS,
    NE,
    NIN,
    OR,
    STARTSWITH,
    SUBSTRING,
    TOLOWER,
    TOUPPER,
)
from odata_v4_query.errors import (
    UnexpectedEmptyArgumentsError,
    UnexpectedNullFiltersError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnexpectedNumberOfArgumentsError,
    UnexpectedTypeError,
    UnknownFunctionError,
    UnknownOperatorError,
)
from odata_v4_query.query_parser import FilterNode


@dataclass(frozen=True, kw_only=True)
class FunctionParser:
    func: Callable[..., FilterNode]
    arg_types: tuple[type, ...] | None = None


class BaseFilterNodeParser(ABC):
    """Base class for filter node parsers.

    The following methods must be implemented by subclasses:

    - **parse_startswith**: Parse a startswith function.
    - **parse_endswith**: Parse an endswith function.
    - **parse_contains**: Parse a contains function.
    - **parse_substring**: Parse a substring function.
    - **parse_tolower**: Parse a tolower function.
    - **parse_toupper**: Parse a toupper function.
    - **parse_membership_operators**: Parse an in/nin operator.
    - **parse_comparison_operators**: Parse an eq/ne/gt/ge/lt/le operator.
    - **parse_has_operator**: Parse a has operator.
    - **parse_and_or_operators**: Parse an and/or operator.
    - **parse_not_nor_operators**: Parse a not/nor operator.
    """

    def __init__(self) -> None:
        self._functions_map = {
            STARTSWITH: FunctionParser(func=self.parse_startswith, arg_types=(str,)),
            ENDSWITH: FunctionParser(func=self.parse_endswith, arg_types=(str,)),
            CONTAINS: FunctionParser(func=self.parse_contains, arg_types=(str,)),
            SUBSTRING: FunctionParser(
                func=self.parse_substring,
                arg_types=(int, int),
            ),
            TOLOWER: FunctionParser(func=self.parse_tolower),
            TOUPPER: FunctionParser(func=self.parse_toupper),
        }

    @abstractmethod
    def parse_startswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_endswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_contains(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_substring(self, field: str, start: int, length: int) -> FilterNode: ...

    @abstractmethod
    def parse_tolower(self, field: str) -> FilterNode: ...

    @abstractmethod
    def parse_toupper(self, field: str) -> FilterNode: ...

    @abstractmethod
    def parse_membership_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode: ...

    @abstractmethod
    def parse_comparison_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode: ...

    @abstractmethod
    def parse_has_operator(self, left: Any, op_node: Any, right: Any) -> FilterNode: ...

    @abstractmethod
    def parse_and_or_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode: ...

    @abstractmethod
    def parse_not_nor_operators(self, op_node: Any, right: Any) -> FilterNode: ...

    def parse(self, filter_node: FilterNode) -> Any:
        """Parse an AST to an ORM/ODM filter expression from the root node.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        Any
            ORM/ODM filter expression.

        Raises
        ------
        UnexpectedNullFiltersError
            If the resulting filter is None.

        """
        filters = self.node_to_filter_expr(filter_node).value
        if filters is None:
            raise UnexpectedNullFiltersError(repr(filter_node))

        return filters

    def node_to_filter_expr(self, filter_node: FilterNode) -> FilterNode:
        """Recursively convert a filter node to an ORM/ODM filter expression.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        FilterNode
            New filter node containing the resulting ORM/ODM filter.

        """
        if filter_node.type_ == 'function':
            return self.parse_function_node(filter_node)

        if filter_node.type_ == 'operator':
            left = None
            if filter_node.left is not None:
                left = self.node_to_filter_expr(filter_node.left)

            right = None
            if filter_node.right is not None:
                right = self.node_to_filter_expr(filter_node.right)

            return self.parse_operator_node(filter_node, left, right)

        return filter_node

    def parse_function_node(self, func_node: FilterNode) -> FilterNode:
        """Parse a function node to an ORM/ODM filter expression.

        Parameters
        ----------
        func_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        FilterNode
            New filter node containing the resulting ORM/ODM filter.

        Raises
        ------
        UnexpectedNullFunctionNameError
            If function name is None.
        UnexpectedEmptyArgumentsError
            If arguments of the function are empty.
        UnexpectedNullOperandError
            If an operand is None.
        UnknownFunctionError
            If the function is unknown.
        UnexpectedNumberOfArgumentsError
            If the number of arguments does not match the expected number.

        """
        if not func_node.value:
            raise UnexpectedNullFunctionNameError(repr(func_node))

        if not func_node.arguments:
            raise UnexpectedEmptyArgumentsError(func_node.value)

        parser = self._functions_map.get(func_node.value)
        if parser is None:
            raise UnknownFunctionError(func_node.value)

        expected_args = FUNCTION_ARITY[func_node.value]
        if len(func_node.arguments) != expected_args:
            raise UnexpectedNumberOfArgumentsError(
                func_node.value,
                expected_args,
                len(func_node.arguments),
            )

        field = func_node.arguments[0].value
        if field is None:
            raise UnexpectedNullOperandError(func_node.value)

        return self._get_function_node(func_node.value, field, func_node.arguments[1:])

    def parse_operator_node(
        self,
        op_node: FilterNode,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        """Parse an operator node to an ORM/ODM filter expression.

        Parameters
        ----------
        op_node : FilterNode
            AST representing the parsed filter expression.
        left : FilterNode | None
            Left operand.
        right : FilterNode | None
            Right operand.

        Returns
        -------
        FilterNode
            New filter node containing the resulting ORM/ODM filter.

        Raises
        ------
        UnexpectedNullOperatorError
            If the operator is None.
        UnexpectedNullOperandError
            If an required operand is None.
        UnknownOperatorError
            If the operator is unknown.

        """
        if op_node.value is None:
            raise UnexpectedNullOperatorError(repr(op_node))

        if op_node.value in COMPARISON_OPERATORS:
            return self._parse_comparison_or_membership(op_node.value, left, right)

        if op_node.value == HAS:
            return self._parse_has(op_node.value, left, right)

        if op_node.value in LOGICAL_OPERATORS:
            return self._parse_logical(op_node.value, left, right)

        raise UnknownOperatorError(op_node.value)

    def _get_function_node(
        self,
        function_name: str,
        field: str,
        arguments: list[Any],
    ) -> FilterNode:
        parser = self._functions_map.get(function_name)
        if parser is None:  # pragma: no cover
            raise UnknownFunctionError(function_name)
        if not parser.arg_types:  # pragma: no cover
            return parser.func(field)
        if len(arguments) != len(parser.arg_types):  # pragma: no cover
            raise UnexpectedNumberOfArgumentsError(
                function_name,
                len(parser.arg_types),
                len(arguments),
            )
        args = []
        for i in range(len(parser.arg_types)):
            value = arguments[i].value
            if value is None:
                raise UnexpectedNullOperandError(function_name)
            type_ = parser.arg_types[i]
            try:
                value = type_(value)
            except ValueError as e:
                raise UnexpectedTypeError(function_name, type_.__name__, value) from e
            args.append(value)
        return parser.func(field, *args)

    def _parse_comparison_or_membership(
        self,
        operator: str,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        if left is None or right is None:
            raise UnexpectedNullOperandError(operator)

        if operator in (IN, NIN):
            if left.value is None or right.arguments is None:
                raise UnexpectedNullOperandError(operator)

            right.value = [arg.value for arg in right.arguments]
            return self.parse_membership_operators(
                left.value,
                operator,
                right.value,
            )

        if left.value is None or (operator not in (EQ, NE) and right.value is None):
            raise UnexpectedNullOperandError(operator)

        return self.parse_comparison_operators(
            left.value,
            operator,
            right.value,
        )

    def _parse_logical(
        self,
        operator: str,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        if operator in (AND, OR):
            if (
                left is None
                or right is None
                or left.value is None
                or right.value is None
            ):
                raise UnexpectedNullOperandError(operator)

            return self.parse_and_or_operators(
                left.value,
                operator,
                right.value,
            )

        if right is None or right.value is None:
            raise UnexpectedNullOperandError(operator)

        return self.parse_not_nor_operators(operator, right.value)

    def _parse_has(
        self,
        operator: str,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        if left is None or right is None or left.value is None or right.value is None:
            raise UnexpectedNullOperandError(operator)

        return self.parse_has_operator(left.value, operator, right.value)

    def _get_value_filter_node(self, value: Any) -> FilterNode:
        return FilterNode(type_='value', value=value)
