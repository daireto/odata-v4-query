"""SQLAlchemy filter node parser."""

from typing import Any, TypeVar

from sqlalchemy import func, not_
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
        super().__init__()
        self.model = model

    def parse(self, filter_node: FilterNode) -> BooleanClauseList:
        """Parse an AST to a SQLAlchemy filter expression.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        BooleanClauseList
            SQLAlchemy filter expression.

        Notes
        -----
        The ``has`` and ``nor`` operators are not supported in SQL,
        so they are converted to a LIKE and NOT expressions,
        respectively.

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

                if isinstance(left.value, str):
                    self._current_field_path = left.value
                    left.value = self._resolve_field_path(left.value)

            right = None
            if filter_node.right is not None:
                right = self.node_to_filter_expr(filter_node.right)

            result = self.parse_operator_node(filter_node, left, right)
            self._current_field_path = None
            return result

        return filter_node

    def parse_startswith(self, field: str, value: Any) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        expr_value = column.ilike(f'{value}%')
        if '/' in field:
            self._current_field_path = field
        result = self._get_value_filter_node(expr_value)
        if '/' in field:
            result.value = self._build_nested_filter(field, result.value)
            self._current_field_path = None
        return result

    def parse_endswith(self, field: str, value: Any) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        expr_value = column.ilike(f'%{value}')
        if '/' in field:
            self._current_field_path = field
        result = self._get_value_filter_node(expr_value)
        if '/' in field:
            result.value = self._build_nested_filter(field, result.value)
            self._current_field_path = None
        return result

    def parse_contains(self, field: str, value: Any) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        expr_value = column.ilike(f'%{value}%')
        if '/' in field:
            self._current_field_path = field
        result = self._get_value_filter_node(expr_value)
        if '/' in field:
            result.value = self._build_nested_filter(field, result.value)
            self._current_field_path = None
        return result

    def parse_substring(self, field: str, start: int, length: int) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        if length < 0:
            expr_value = func.substr(column, start + 1)
        else:
            expr_value = func.substr(column, start + 1, length)
        return self._get_value_filter_node(expr_value)

    def parse_tolower(self, field: str) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        expr_value = func.lower(column)
        if '/' in field:
            self._current_field_path = field
        return self._get_value_filter_node(expr_value)

    def parse_toupper(self, field: str) -> FilterNode:
        column = self._resolve_field_path(field)  # type: ignore
        expr_value = func.upper(column)
        if '/' in field:
            self._current_field_path = field
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

    def _parse_comparison_or_membership(
        self,
        operator: str,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        """Override to handle nested fields with has()."""
        result = super()._parse_comparison_or_membership(operator, left, right)

        if (
            hasattr(self, '_current_field_path')
            and self._current_field_path
            and '/' in self._current_field_path
        ):
            result.value = self._build_nested_filter(
                self._current_field_path,
                result.value,
            )

        return result

    def _to_sql_operator(self, operator: str) -> OperatorType:
        """Convert an OData operator to a SQLAlchemy operator.

        Parameters
        ----------
        operator : str
            OData operator.

        Returns
        -------
        OperatorType
            SQLAlchemy operator.

        """
        sql_operator = OPERATORS_MAP.get(operator)
        if sql_operator:
            return sql_operator
        raise UnknownOperatorError(operator)  # pragma: no cover

    def _resolve_field_path(self, field_path: str) -> Any:
        """Resolve a field path to a SQLAlchemy column or relationship attribute.

        Converts OData path notation (e.g., 'Customer/Name') to SQLAlchemy
        attribute access (e.g., Customer.Name).

        Parameters
        ----------
        field_path : str
            Field path using OData notation with '/' as separator.

        Returns
        -------
        Any
            SQLAlchemy column or relationship attribute.

        Examples
        --------
        >>> parser._resolve_field_path('name')
        User.name
        >>> parser._resolve_field_path('user/name')
        User.name (from the related User model)

        """
        if '/' not in field_path:
            return getattr(self.model, field_path)

        parts = field_path.split('/')
        current_model = self.model

        for part in parts[:-1]:  # Exclude the field name
            attr = getattr(current_model, part)
            if hasattr(attr.property, 'mapper'):
                current_model = attr.property.mapper.class_
            else:
                current_model = attr  # pragma: no cover

        return getattr(current_model, parts[-1])

    def _build_nested_filter(self, field_path: str, filter_expr: Any) -> Any:
        """Build a nested filter using has() for relationships.

        Supports multiple levels of nesting by wrapping the filter expression
        with has() for each relationship in the path. The method builds the
        nested structure from innermost to outermost by reversing the
        relationship chain.

        Parameters
        ----------
        field_path : str
            Field path using OData notation with '/' as separator
            (e.g., 'user/name', 'user/profile/address/city').
        filter_expr : Any
            The filter expression to apply on the nested field.

        Returns
        -------
        Any
            SQLAlchemy filter expression using has() for relationships.

        Examples
        --------
        Single level: The filter expression is wrapped in has() for the relationship.
        >>> from odata_v4_query.utils.filter_parsers.sql_filter_parser import SQLAlchemyFilterNodeParser
        >>> parser = SQLAlchemyFilterNodeParser(User)
        >>> parser._build_nested_filter('profile/bio', Profile.bio == 'Software Engineer')
        User.has(Profile.bio == 'Software Engineer')

        Multi-level: The relationships are wrapped in reverse order to build the correct
        nested structure from the deepest level outward.
        >>> from odata_v4_query.utils.filter_parsers.sql_filter_parser import SQLAlchemyFilterNodeParser
        >>> parser = SQLAlchemyFilterNodeParser(User)
        >>> parser._build_nested_filter('user/profile/address/city', Address.city == 'NYC')
        User.has(Profile.has(Address.has(Address.city == 'NYC')))

        """
        if '/' not in field_path:
            return filter_expr  # pragma: no cover

        parts = field_path.split('/')
        model_and_relationship_tuples = []
        current_model = self.model

        for part in parts[:-1]:  # Exclude the field name
            relationship = getattr(current_model, part)
            model_and_relationship_tuples.append((current_model, relationship))
            if hasattr(relationship.property, 'mapper'):
                current_model = relationship.property.mapper.class_

        # Build the has() chain from innermost to outermost
        result = filter_expr
        for _, relationship in reversed(model_and_relationship_tuples):
            result = relationship.has(result)

        return result
