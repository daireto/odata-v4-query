from typing import Any, Literal, TypeVar, overload

from beanie import Document
from beanie.odm.queries.aggregation import AggregationQuery
from beanie.odm.queries.find import FindMany
from beanie.operators import Or
from pydantic import BaseModel

from odata_v4_query.errors import ParseError, UnexpectedNullOperand
from odata_v4_query.query_parser import FilterNode, ODataQueryOptions

FindQueryProjectionType = TypeVar('FindQueryProjectionType', bound=BaseModel)
FindType = TypeVar('FindType', bound=Document)
Query = (
    FindMany[FindType]
    | AggregationQuery[dict[str, Any]]
    | AggregationQuery[FindQueryProjectionType]
)

ODATA_COMPARISON_OPERATORS = ('eq', 'ne', 'gt', 'ge', 'lt', 'le', 'in', 'nin')
ODATA_LOGICAL_OPERATORS = ('and', 'or', 'not', 'nor')


class _BeanieFilterNodeParser:
    """Parser for converting OData filter AST to MongoDB filter."""

    def parse_filter(self, filter_node: FilterNode):
        """Parses a filter node and returns a MongoDB filter.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        Any
            MongoDB filter expression.
        """
        return self._filter_node_to_beanie_filter(filter_node).value

    def _filter_node_to_beanie_filter(
        self, filter_node: FilterNode
    ) -> FilterNode:
        """Converts a filter node to a MongoDB filter.

        Parameters
        ----------
        filter_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        FilterNode
            New filter node containing the MongoDB filter.
        """
        if filter_node.type_ == 'function':
            return self._parse_function_node(filter_node)

        if filter_node.type_ == 'operator':
            left = None
            if filter_node.left:
                left = self._filter_node_to_beanie_filter(filter_node.left)

            right = None
            if filter_node.right:
                right = self._filter_node_to_beanie_filter(filter_node.right)

            return self._parse_operator_node(filter_node, left, right)

        return filter_node

    def _parse_operator_node(
        self,
        op_node: FilterNode,
        left: FilterNode | None,
        right: FilterNode | None,
    ) -> FilterNode:
        """Parses an operator node and returns a MongoDB filter.

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
            New filter node containing the MongoDB filter.

        Raises
        ------
        ParseError
            If the operator is unknown.
        ParseError
            If a required operand is None.
        """
        if op_node.value in ODATA_COMPARISON_OPERATORS:
            if not left or not right:
                raise UnexpectedNullOperand(op_node.value)

            if op_node.value in ('in', 'nin'):
                if not left.value or not right.arguments:
                    raise UnexpectedNullOperand(op_node.value)

                right.value = [arg.value for arg in right.arguments]
                operator = self._to_mongo_comparison_operator(op_node.value)
                return FilterNode(
                    type_='value',
                    value={left.value: {operator: right.value}},
                )

            if not left.value or not right.value:
                raise UnexpectedNullOperand(op_node.value)

            operator = self._to_mongo_comparison_operator(op_node.value)
            return FilterNode(
                type_='value',
                value={left.value: {operator: right.value}},
            )

        elif op_node.value == 'has':
            if not left or not right or not left.value or not right.value:
                raise UnexpectedNullOperand(op_node.value)

            return FilterNode(type_='value', value={left.value: right.value})

        elif op_node.value in ODATA_LOGICAL_OPERATORS:
            if op_node.value in ('and', 'or'):
                if not left or not right or not left.value or not right.value:
                    raise UnexpectedNullOperand(op_node.value)

                operator = self._to_mongo_comparison_operator(op_node.value)
                value = {operator: [left.value, right.value]}

            if op_node.value in ('not', 'nor'):
                if not right or not right.value:
                    raise UnexpectedNullOperand(op_node.value)

                operator = self._to_mongo_comparison_operator(op_node.value)
                field, comparison = right.value.popitem()
                value = {field: {operator: comparison}}

            return FilterNode(type_='value', value=value)

        else:
            raise ParseError(f'unknown operator: {op_node.value!r}')

    def _parse_function_node(self, func_node: FilterNode) -> FilterNode:
        """Parses a function node and returns a MongoDB filter.

        Parameters
        ----------
        func_node : FilterNode
            AST representing the parsed filter expression.

        Returns
        -------
        FilterNode
            New filter node containing the MongoDB filter.

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

        if not func_node.value or not func_node.arguments:
            raise ParseError(
                f'unexpected empty arguments for function {func_node.value!r}'
            )

        if not len(func_node.arguments) == 2:
            raise ParseError(
                f'expected 2 arguments for function {func_node.value!r}'
            )

        if (
            not func_node.arguments[0].value
            or not func_node.arguments[1].value
        ):
            raise ParseError(
                f'unexpected null operand for function {func_node.value!r}'
            )

        if func_node.value == 'startswith':
            value = {
                func_node.arguments[0].value: {
                    '$regex': f'^{func_node.arguments[1].value}',
                    '$options': 'i',
                }
            }
        elif func_node.value == 'endswith':
            value = {
                func_node.arguments[0].value: {
                    '$regex': f'{func_node.arguments[1].value}$',
                    '$options': 'i',
                }
            }
        elif func_node.value == 'contains':
            value = {
                func_node.arguments[0].value: {
                    '$regex': func_node.arguments[1].value,
                    '$options': 'i',
                }
            }
        else:
            raise ParseError(f'unknown function: {func_node.value!r}')

        return FilterNode(type_='value', value=value)

    def _to_mongo_comparison_operator(self, operator: str) -> str | None:
        """Converts an OData comparison operator to a MongoDB operator.

        Parameters
        ----------
        operator : str
            OData comparison operator.

        Returns
        -------
        str
            MongoDB operator.
        None
            If the operator is unknown.

        Raises
        ------
        ParseError
            If the operator is unknown.
        """
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


@overload
def apply_to_beanie_query(
    document_or_query: type[FindType] | FindMany[FindType],
    options: ODataQueryOptions,
    projection_model: None = None,
    parse_select: Literal[False] = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> FindMany[FindType]: ...


@overload
def apply_to_beanie_query(
    document_or_query: type[FindType] | FindMany[FindType],
    options: ODataQueryOptions,
    projection_model: type[FindQueryProjectionType],
    parse_select: Literal[False] = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> FindMany[FindQueryProjectionType]: ...


@overload
def apply_to_beanie_query(
    document_or_query: type[FindType] | FindMany[FindType],
    options: ODataQueryOptions,
    projection_model: None = None,
    parse_select: Literal[True] = True,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> AggregationQuery[dict[str, Any]]: ...


@overload
def apply_to_beanie_query(
    document_or_query: type[FindType] | FindMany[FindType],
    options: ODataQueryOptions,
    projection_model: type[FindQueryProjectionType],
    parse_select: Literal[True] = True,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> AggregationQuery[FindQueryProjectionType]: ...


def apply_to_beanie_query(
    document_or_query: type[FindType] | FindMany[FindType],
    options: ODataQueryOptions,
    projection_model: type[FindQueryProjectionType] | None = None,
    parse_select: bool = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> Query:
    """Applies OData query options to a Beanie query.

    .. note::
        The ``$count``, ``$expand`` and ``$format`` options
        are not supported.

    Parameters
    ----------
    document_or_query : type[FindType] | FindMany[FindType]
        Document class or query to apply options to.
        If a class is provided, a new query is created
        by calling ``find()``.
    options : ODataQueryOptions
        Parsed query options.
    projection_model : type[FindQueryProjectionType] | None, optional
        Projection model, by default None.
    parse_select : bool, optional
        If True, ``$select`` is parsed and applied as a projection,
        by default False.
    search_fields : list[str] | None, optional
        Fields to search in if ``$search`` is used, by default None.
    fetch_links : bool, optional
        Whether to fetch links, by default False.

    Returns
    -------
    Query
        Beanie query with applied options.

    Raises
    ------
    ParseError
        If the filters are empty.
    """
    if isinstance(document_or_query, FindMany):
        query = document_or_query
    else:
        query = document_or_query.find()

    if options.skip:
        query = query.skip(options.skip)

    if options.top:
        query = query.limit(options.top)

    if options.filter_:
        parser = _BeanieFilterNodeParser()
        filters = parser.parse_filter(options.filter_)
        if not filters:
            raise ParseError('unexpected null filters')

        query = query.find(filters, fetch_links=fetch_links)

    if options.search and search_fields:
        query = query.find(
            Or(
                *[
                    {field: {'$regex': options.search}}
                    for field in search_fields
                ]
            ).query,
            fetch_links=fetch_links,
        )

    if options.orderby:
        sort_args: list[str] = []
        for item in options.orderby:
            sort_symbol = '-' if item.direction == 'desc' else '+'
            sort_args.append(f'{sort_symbol}{item.field}')
        query = query.sort(*sort_args)

    if options.select and parse_select:
        query = query.aggregate(
            [{'$project': {field: 1 for field in options.select}}],
            projection_model=projection_model,
        )
    else:
        query = query.project(projection_model)

    return query
