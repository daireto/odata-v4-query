"""MongoDB filter node parser."""

from typing import Any

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
from odata_v4_query.errors import (
    AggregationOperatorNotSupportedError,
    UnknownOperatorError,
)
from odata_v4_query.query_parser import FilterNode

from .base_filter_parser import BaseFilterNodeParser


class MongoDBFilterNodeParser(BaseFilterNodeParser):
    """Parser for converting OData filter AST to MongoDB filter.

    See the ``parse()`` method for more information.
    """

    def parse(self, filter_node: FilterNode) -> dict[str, Any]:
        """Parse an AST to a MongoDB filter.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        dict[str, Any]
            MongoDB filter expression.

        Examples
        --------
        >>> from odata_v4_query import ODataFilterParser
        >>> from odata_v4_query.utils.filter_parsers import MongoDBFilterNodeParser
        >>> parser = ODataFilterParser()
        >>> ast = parser.parse("name eq 'John' and age gt 25")
        >>> MongoDBFilterNodeParser().parse(ast)
        {'$and': [{'name': {'$eq': 'John'}}, {'age': {'$gt': 25}}]}

        """
        return super().parse(filter_node)

    def parse_startswith(self, field: str, value: Any) -> FilterNode:
        field = self._normalize_field_path(field)
        expr_value = {
            field: {
                '$regex': f'^{value}',
                '$options': 'i',
            },
        }
        return self._get_value_filter_node(expr_value)

    def parse_endswith(self, field: str, value: Any) -> FilterNode:
        field = self._normalize_field_path(field)
        expr_value = {
            field: {
                '$regex': f'{value}$',
                '$options': 'i',
            },
        }
        return self._get_value_filter_node(expr_value)

    def parse_contains(self, field: str, value: Any) -> FilterNode:
        field = self._normalize_field_path(field)
        expr_value = {
            field: {
                '$regex': value,
                '$options': 'i',
            },
        }
        return self._get_value_filter_node(expr_value)

    def parse_substring(self, *_) -> FilterNode:
        func_name = 'substring'
        op = '$substr'
        raise AggregationOperatorNotSupportedError(func_name, op)

    def parse_tolower(self, *_) -> FilterNode:
        func_name = 'tolower'
        op = '$toLower'
        raise AggregationOperatorNotSupportedError(func_name, op)

    def parse_toupper(self, *_) -> FilterNode:
        func_name = 'toupper'
        op = '$toUpper'
        raise AggregationOperatorNotSupportedError(func_name, op)

    def parse_membership_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        field = self._normalize_field_path(left) if isinstance(left, str) else left
        return FilterNode(type_='value', value={field: {operator: right}})

    def parse_comparison_operators(
        self,
        left: Any,
        op_node: Any,
        right: Any,
    ) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        field = self._normalize_field_path(left) if isinstance(left, str) else left
        return FilterNode(type_='value', value={field: {operator: right}})

    def parse_has_operator(self, left: Any, _: Any, right: Any) -> FilterNode:
        field = self._normalize_field_path(left) if isinstance(left, str) else left
        return FilterNode(type_='value', value={field: right})

    def parse_and_or_operators(self, left: Any, op_node: Any, right: Any) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        value = {operator: [left, right]}
        return FilterNode(type_='value', value=value)

    def parse_not_nor_operators(self, op_node: Any, right: Any) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        field, comparison = right.popitem()
        value = {field: {operator: comparison}}
        return FilterNode(type_='value', value=value)

    def _to_mongo_operator(self, operator: str) -> str:
        """Convert an OData operator to a MongoDB operator.

        Parameters
        ----------
        operator : str
            OData operator.

        Returns
        -------
        str
            MongoDB operator.

        """
        if operator == GE:
            return '$gte'
        if operator == LE:
            return '$lte'
        if operator in (EQ, NE, GT, LT, IN, NIN, AND, OR, NOT, NOR):
            return f'${operator}'
        raise UnknownOperatorError(operator)  # pragma: no cover

    def _normalize_field_path(self, field: str) -> str:
        """Convert OData path separator (/) to MongoDB dot notation (.).

        Parameters
        ----------
        field : str
            Field path using OData notation (e.g., 'Customer/Name').

        Returns
        -------
        str
            Field path using MongoDB dot notation (e.g., 'Customer.Name').

        """
        return field.replace('/', '.')
