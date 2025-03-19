"""MongoDB filter node parser."""

from typing import Any

from odata_v4_query.errors import ParseError
from odata_v4_query.query_parser import FilterNode

from .base_filter_parser import BaseFilterNodeParser


class MongoDBFilterNodeParser(BaseFilterNodeParser):
    """Parser for converting OData filter AST to MongoDB filter.

    See the ``parse()`` method for more information.
    """

    def parse(self, filter_node: FilterNode) -> dict[str, Any]:
        """Parses a filter node and returns a MongoDB filter.

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
        expr_value = {
            field: {
                '$regex': f'^{value}',
                '$options': 'i',
            }
        }
        return self._get_value_filter_node(expr_value)

    def parse_endswith(self, field: str, value: Any) -> FilterNode:
        expr_value = {
            field: {
                '$regex': f'{value}$',
                '$options': 'i',
            }
        }
        return self._get_value_filter_node(expr_value)

    def parse_contains(self, field: str, value: Any) -> FilterNode:
        expr_value = {
            field: {
                '$regex': value,
                '$options': 'i',
            }
        }
        return self._get_value_filter_node(expr_value)

    def parse_in_nin_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        return FilterNode(type_='value', value={left: {operator: right}})

    def parse_comparison_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        return FilterNode(type_='value', value={left: {operator: right}})

    def parse_has_operator(self, left: Any, _: Any, right: Any) -> FilterNode:
        return FilterNode(type_='value', value={left: right})

    def parse_and_or_operators(
        self, left: Any, op_node: Any, right: Any
    ) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        value = {operator: [left, right]}
        return FilterNode(type_='value', value=value)

    def parse_not_nor_operators(self, op_node: Any, right: Any) -> FilterNode:
        operator = self._to_mongo_operator(op_node)
        field, comparison = right.popitem()
        value = {field: {operator: comparison}}
        return FilterNode(type_='value', value=value)

    def _to_mongo_operator(self, operator: str) -> str:
        match operator:
            case 'ge':
                return '$gte'
            case 'le':
                return '$lte'
            case (
                'eq'
                | 'ne'
                | 'gt'
                | 'lt'
                | 'in'
                | 'nin'
                | 'and'
                | 'or'
                | 'not'
                | 'nor'
            ):
                return f'${operator}'
            case _:  # pragma: no cover
                raise ParseError(f'unknown operator: {operator!r}')  # pragma: no cover
