"""Base class for filter node parsers."""

from abc import ABC, abstractmethod
from typing import Any

from odata_v4_query.definitions import (
    AND,
    COMPARISON_OPERATORS,
    CONTAINS,
    ENDSWITH,
    EQ,
    HAS,
    IN,
    LOGICAL_OPERATORS,
    NE,
    NIN,
    OR,
    STARTSWITH,
)
from odata_v4_query.errors import (
    TwoArgumentsExpectedError,
    UnexpectedEmptyArgumentsError,
    UnexpectedNullFiltersError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnknownFunctionError,
    UnknownOperatorError,
)
from odata_v4_query.query_parser import FilterNode

_TWO_ARGUMENTS_VALUE = 2


class BaseFilterNodeParser(ABC):
    """Base class for filter node parsers.

    The following methods must be implemented by subclasses:

    - **parse_startswith**: Parse a startswith function.
    - **parse_endswith**: Parse an endswith function.
    - **parse_contains**: Parse a contains function.
    - **parse_membership_operators**: Parse an in/nin operator.
    - **parse_comparison_operators**: Parse an eq/ne/gt/ge/lt/le operator.
    - **parse_has_operator**: Parse a has operator.
    - **parse_and_or_operators**: Parse an and/or operator.
    - **parse_not_nor_operators**: Parse a not/nor operator.
    """

    @abstractmethod
    def parse_startswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_endswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_contains(self, field: str, value: Any) -> FilterNode: ...

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
        TwoArgumentsExpectedError
            If the function expects 2 arguments and more than 2 are provided.
        UnexpectedNullOperandError
            If an operand is None.
        UnknownFunctionError
            If the function is unknown.

        """
        if not func_node.value:
            raise UnexpectedNullFunctionNameError(repr(func_node))

        if not func_node.arguments:
            raise UnexpectedEmptyArgumentsError(func_node.value)

        if not self._has_two_arguments(func_node.arguments):
            raise TwoArgumentsExpectedError(func_node.value)

        field, value = (
            func_node.arguments[0].value,
            func_node.arguments[1].value,
        )
        if field is None or value is None:
            raise UnexpectedNullOperandError(func_node.value)

        if func_node.value == STARTSWITH:
            return self.parse_startswith(field, value)

        if func_node.value == ENDSWITH:
            return self.parse_endswith(field, value)

        if func_node.value == CONTAINS:
            return self.parse_contains(field, value)

        raise UnknownFunctionError(func_node.value)

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

    def _has_two_arguments(self, arguments: list[FilterNode]) -> bool:
        return len(arguments) == _TWO_ARGUMENTS_VALUE

    def _get_value_filter_node(self, value: Any) -> FilterNode:
        return FilterNode(type_='value', value=value)
