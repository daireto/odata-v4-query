"""Utility function for applying OData query options to a Beanie query.

See ``apply_to_beanie_query()`` for more information.
"""

try:
    from beanie import Document
    from beanie.odm.queries.aggregation import AggregationQuery
    from beanie.odm.queries.find import FindMany
    from beanie.operators import Or
except ImportError:  # pragma: no cover
    raise ImportError(
        'The beanie dependency is not installed. '
        'Install it with `pip install odata-v4-query[beanie]` '
        'or install it directly with `pip install beanie`.'
    )  # pragma: no cover

from typing import Any, Literal, TypeVar, overload

from pydantic import BaseModel

from odata_v4_query.query_parser import ODataQueryOptions

from ._func import compute_skip_from_page
from .filter_parsers.mongo_filter_parser import MongoDBFilterNodeParser

FindQueryProjectionType = TypeVar('FindQueryProjectionType', bound=BaseModel)
FindType = TypeVar('FindType', bound=Document)
ParsedQuery = (
    FindMany[FindType]
    | AggregationQuery[dict[str, Any]]
    | AggregationQuery[FindQueryProjectionType]
)


@overload
def apply_to_beanie_query(
    options: ODataQueryOptions,
    document_or_query: type[FindType] | FindMany[FindType],
    projection_model: None = None,
    parse_select: Literal[False] = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> FindMany[FindType]: ...


@overload
def apply_to_beanie_query(
    options: ODataQueryOptions,
    document_or_query: type[FindType] | FindMany[FindType],
    projection_model: type[FindQueryProjectionType],
    parse_select: Literal[False] = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> FindMany[FindQueryProjectionType]: ...


@overload
def apply_to_beanie_query(
    options: ODataQueryOptions,
    document_or_query: type[FindType] | FindMany[FindType],
    projection_model: None = None,
    parse_select: Literal[True] = True,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> AggregationQuery[dict[str, Any]]: ...


@overload
def apply_to_beanie_query(
    options: ODataQueryOptions,
    document_or_query: type[FindType] | FindMany[FindType],
    projection_model: type[FindQueryProjectionType],
    parse_select: Literal[True] = True,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> AggregationQuery[FindQueryProjectionType]: ...


def apply_to_beanie_query(
    options: ODataQueryOptions,
    document_or_query: type[FindType] | FindMany[FindType],
    projection_model: type[FindQueryProjectionType] | None = None,
    parse_select: bool = False,
    search_fields: list[str] | None = None,
    fetch_links: bool = False,
) -> ParsedQuery:
    """Applies OData query options to a Beanie query.

    If the ``$page`` option is used, it is converted to ``$skip``
    and ``$top``. If ``$top`` is not provided, it defaults to 100.
    The ``$skip`` is computed as ``(page - 1) * top``. If ``$skip``
    is provided, it is overwritten.

    The ``$search`` option is only supported if ``search_fields``
    is provided.

    The ``$select`` option is only supported if ``parse_select``
    is True. If ``projection_model`` is provided, the results
    are projected with a Pydantic model, otherwise a dictionary.

    .. note::
        The ``$count``, ``$expand`` and ``$format`` options
        won't be applied. You need to handle them manually.

    Parameters
    ----------
    options : ODataQueryOptions
        Parsed query options.
    document_or_query : type[FindType] | FindMany[FindType]
        Document class or query to apply options to.
        If a class is provided, a new query is created
        by calling ``find()``.
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
    ParsedQuery
        Beanie query with applied options.

    Raises
    ------
    ParseError
        If the filters are empty.

    Examples
    --------
    Assuming the following ``User`` beanie document:
    >>> from beanie import Document
    >>> class User(Document):
    ...     name: str
    ...     email: str
    ...     age: int

    Create a new query with applied options:
    >>> from odata_v4_query import ODataQueryParser
    >>> from odata_v4_query.utils.beanie import apply_to_beanie_query
    >>> parser = ODataQueryParser()
    >>> options = parser.parse_query_string('$top=10&$skip=20')
    >>> query = apply_to_beanie_query(options, User)

    Apply options to an existing query:
    >>> query = apply_to_beanie_query(options, User.find())

    Apply options with projection:
    >>> from pydantic import BaseModel
    >>> class UserProjection(BaseModel):
    ...     name: str
    ...     email: str
    >>> query = apply_to_beanie_query(
    ...     options,
    ...     User.find(),
    ...     projection_model=UserProjection
    ... )

    Apply options with projection and parsing ``$select``:
    >>> query = apply_to_beanie_query(
    ...     options,
    ...     User.find(),
    ...     projection_model=UserProjection,
    ...     parse_select=True
    ... )

    Apply ``$search`` option:
    >>> query = apply_to_beanie_query(
    ...     options,
    ...     User.find(),
    ...     search_fields=['name', 'email']
    ... )

    Fetch links:
    >>> query = apply_to_beanie_query(
    ...     options,
    ...     User.find(),
    ...     fetch_links=True
    ... )
    """
    compute_skip_from_page(options)

    if isinstance(document_or_query, FindMany):
        query = document_or_query
    else:
        query = document_or_query.find()

    if options.skip:
        query = query.skip(options.skip)

    if options.top:
        query = query.limit(options.top)

    if options.filter_:
        parser = MongoDBFilterNodeParser()
        filters = parser.parse(options.filter_)
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
        sort_args = []
        for item in options.orderby:
            direction = '-' if item.direction == 'desc' else '+'
            sort_args.append(f'{direction}{item.field}')
        query = query.sort(*sort_args)

    if options.select and parse_select:
        query = query.aggregate(
            [{'$project': {field: 1 for field in options.select}}],
            projection_model=projection_model,
        )
    else:
        query = query.project(projection_model)

    return query
