"""Base class for filter node parsers."""

from abc import ABC, abstractmethod
from typing import Any

from odata_v4_query.definitions import (
    ODATA_COMPARISON_OPERATORS,
    ODATA_LOGICAL_OPERATORS,
)
from odata_v4_query.errors import ParseError, UnexpectedNullOperand
from odata_v4_query.query_parser import FilterNode


class BaseFilterNodeParser(ABC):
    """Base class for filter node parsers.

    The following methods must be implemented by subclasses:
    - **parse_startswith**: Parses a startswith function.
    - **parse_endswith**: Parses an endswith function.
    - **parse_contains**: Parses a contains function.
    - **parse_in_nin_operators**: Parses an in/nin operator.
    - **parse_comparison_operators**: Parses an eq/ne/gt/ge/lt/le operator.
    - **parse_has_operator**: Parses a has operator.
    - **parse_and_or_operators**: Parses an and/or operator.
    - **parse_not_nor_operators**: Parses a not/nor operator.
    """

    @abstractmethod
    def parse_startswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_endswith(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_contains(self, field: str, value: Any) -> FilterNode: ...

    @abstractmethod
    def parse_in_nin_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode: ...

    @abstractmethod
    def parse_comparison_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode: ...

    @abstractmethod
    def parse_has_operator(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode: ...

    @abstractmethod
    def parse_and_or_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode: ...

    @abstractmethod
    def parse_not_nor_operators(
        self, op_node: Any, right: Any
    ) -> FilterNode: ...

    def parse(self, filter_node: FilterNode) -> Any:
        """Parses a filter node and returns the corresponding
        ORM/ODM filter.

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
        ParseError
            If the resulting filter is None.
        """
        filters = self.node_to_filter_expr(filter_node).value
        if filters is None:
            raise ParseError('unexpected null filters')

        return filters

    def node_to_filter_expr(self, filter_node: FilterNode) -> FilterNode:
        """Converts a filter node to an ORM/ODM filter expression.

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
        """Parses a function node and returns the corresponding
        ORM/ODM filter.

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
        ParseError
            If function name is None.
        ParseError
            If arguments of the function are empty.
        ParseError
            If arguments count is not 2.
        ParseError
            If an operand is None.
        ParseError
            If the function is unknown.
        """
        if not func_node.value:
            raise ParseError(f'unexpected null function name: {func_node!r}')

        if not func_node.arguments:
            raise ParseError(
                f'unexpected empty arguments for function {func_node.value!r}'
            )

        if not len(func_node.arguments) == 2:
            raise ParseError(
                f'expected 2 arguments for function {func_node.value!r}'
            )

        field, value = (
            func_node.arguments[0].value,
            func_node.arguments[1].value,
        )
        if field is None or value is None:
            raise ParseError(
                f'unexpected null operand for function {func_node.value!r}'
            )

        if func_node.value == 'startswith':
            return self.parse_startswith(field, value)

        if func_node.value == 'endswith':
            return self.parse_endswith(field, value)

        if func_node.value == 'contains':
            return self.parse_contains(field, value)

        raise ParseError(f'unknown function: {func_node.value!r}')

    def parse_operator_node(
        self,
        op_node: FilterNode,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        """Parses an operator node and returns the corresponding
        ORM/ODM filter.

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
        UnexpectedNullOperand
            If an operand is None.
        UnexpectedNullOperand
            If a value is None.
        ParseError
            If the operator is unknown.
        """
        if op_node.value in ODATA_COMPARISON_OPERATORS:
            if left is None or right is None:
                raise UnexpectedNullOperand(op_node.value)

            if op_node.value in ('in', 'nin'):
                if left.value is None or right.arguments is None:
                    raise UnexpectedNullOperand(op_node.value)

                right.value = [arg.value for arg in right.arguments]
                return self.parse_in_nin_operators(
                    left.value, op_node.value, right.value
                )

            if left.value is None or (
                op_node.value not in ('eq', 'ne') and right.value is None
            ):
                raise UnexpectedNullOperand(op_node.value)

            return self.parse_comparison_operators(
                left.value, op_node.value, right.value
            )

        elif op_node.value == 'has':
            if (
                left is None
                or right is None
                or left.value is None
                or right.value is None
            ):
                raise UnexpectedNullOperand(op_node.value)

            return self.parse_has_operator(
                left.value, op_node.value, right.value
            )

        elif op_node.value in ODATA_LOGICAL_OPERATORS:
            if op_node.value in ('and', 'or'):
                if (
                    left is None
                    or right is None
                    or left.value is None
                    or right.value is None
                ):
                    raise UnexpectedNullOperand(op_node.value)

                return self.parse_and_or_operators(
                    left.value, op_node.value, right.value
                )

            else:
                if right is None or right.value is None:
                    raise UnexpectedNullOperand(op_node.value)

                return self.parse_not_nor_operators(op_node.value, right.value)

        else:
            raise ParseError(f'unknown operator: {op_node.value!r}')

    def _get_value_filter_node(self, value: Any) -> FilterNode:
        return FilterNode(type_='value', value=value)
