"""SQLAlchemy filter node parser."""

from typing import Any, TypeVar

from sqlalchemy import not_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.operators import (
    OperatorType,
    and_,
    eq,
    ge,
    gt,
    in_op,
    le,
    lt,
    ne,
    notin_op,
    or_,
)

from odata_v4_query.definitions import (
    AND,
    EQ,
    GE,
    GT,
    IN,
    LE,
    LT,
    NE,
    NIN,
    NOR,
    NOT,
    OR,
)
from odata_v4_query.errors import UnknownOperatorError
from odata_v4_query.query_parser import FilterNode

from .base_filter_parser import BaseFilterNodeParser

FilterType = TypeVar('FilterType', bound=DeclarativeBase)

OPERATORS_MAP = {
    EQ: eq,
    NE: ne,
    GT: gt,
    GE: ge,
    LT: lt,
    LE: le,
    IN: in_op,
    NIN: notin_op,
    AND: and_,
    OR: or_,
    NOT: not_,
    NOR: not_,
}


class SQLAlchemyFilterNodeParser(BaseFilterNodeParser):
    """Parser for converting OData filter AST to SQLAlchemy filter.

    See the ``parse()`` method for more information.
    """

    def __init__(self, model: type[FilterType]) -> None:
        """Parser for converting OData filter AST to SQLAlchemy filter.

        Parameters
        ----------
        model : type[FilterType]
            A SQLAlchemy model class.

        """
        self.model = model

    def parse(self, filter_node: FilterNode) -> BooleanClauseList:
        """Parse an AST to a SQLAlchemy filter expression.

        .. note::
            The ``has`` and ``nor`` operators are not supported in SQL,
            so they are converted to a LIKE and NOT expressions,
            respectively.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        BooleanClauseList
            SQLAlchemy filter expression.

        Examples
        --------
        >>> from odata_v4_query import ODataFilterParser
        >>> from odata_v4_query.utils.filter_parsers import SQLAlchemyFilterNodeParser
        >>> parser = ODataFilterParser()
        >>> ast = parser.parse("name eq 'John' and age gt 25")
        >>> filters = SQLAlchemyFilterNodeParser(User).parse(ast)
        >>> filters
        'users.name = :name_1 AND users.age > :age_1'
        >>> filters.compile(compile_kwargs={'literal_binds': True})
        "users.name = 'John' AND users.age > 25"

        """
        return super().parse(filter_node)

    def node_to_filter_expr(self, filter_node: FilterNode) -> FilterNode:
        if filter_node.type_ == 'function':
            return self.parse_function_node(filter_node)

        if filter_node.type_ == 'operator':
            left = None
            if filter_node.left is not None:
                left = self.node_to_filter_expr(filter_node.left)
                left.value = (
                    getattr(self.model, left.value)
                    if isinstance(left.value, str)
                    else left.value
                )

            right = None
            if filter_node.right is not None:
                right = self.node_to_filter_expr(filter_node.right)

            return self.parse_operator_node(filter_node, left, right)

        return filter_node

    def parse_startswith(self, field: str, value: Any) -> FilterNode:
        column = getattr(self.model, field)  # type: ignore
        expr_value = column.ilike(f'{value}%')
        return self._get_value_filter_node(expr_value)

    def parse_endswith(self, field: str, value: Any) -> FilterNode:
        column = getattr(self.model, field)  # type: ignore
        expr_value = column.ilike(f'%{value}')
        return self._get_value_filter_node(expr_value)

    def parse_contains(self, field: str, value: Any) -> FilterNode:
        column = getattr(self.model, field)  # type: ignore
        expr_value = column.ilike(f'%{value}%')
        return self._get_value_filter_node(expr_value)

    def parse_membership_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode:
        operator = self._to_sql_operator(op_node)
        return FilterNode(type_='value', value=operator(left, right))

    def parse_comparison_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode:
        if right is None or right == 'null':
            sql_operator = eq(left, None) if op_node == EQ else ne(left, None)
            return FilterNode(type_='value', value=sql_operator)

        operator = self._to_sql_operator(op_node)
        return FilterNode(type_='value', value=operator(left, right))

    def parse_has_operator(self, left: Any, _: Any, right: Any) -> FilterNode:
        return FilterNode(type_='value', value=left.ilike(f'%{right}%'))

    def parse_and_or_operators(self, left: Any, op_node: Any, right: Any) -> FilterNode:
        operator = self._to_sql_operator(op_node)
        value = operator(left, right)
        return FilterNode(type_='value', value=value)

    def parse_not_nor_operators(self, op_node: Any, right: Any) -> FilterNode:
        operator = self._to_sql_operator(op_node)
        value = operator(right)
        return FilterNode(type_='value', value=value)

    def _to_sql_operator(self, operator: str) -> OperatorType:
        sql_operator = OPERATORS_MAP.get(operator)
        if sql_operator:
            return sql_operator
        raise UnknownOperatorError(operator)  # pragma: no cover
