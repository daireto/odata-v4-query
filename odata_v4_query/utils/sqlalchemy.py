"""Utility function for applying OData query options to a SQLAlchemy query.

See ``apply_to_sqlalchemy_query()`` for more information.
"""

try:
    from sqlalchemy.orm import joinedload
    from sqlalchemy.sql import Select, or_, select
    from sqlalchemy.sql.functions import func
except ImportError as e:  # pragma: no cover
    missing_dep_msg = (
        'The sqlalchemy dependency is not installed. '
        'Install it with `pip install odata-v4-query[sqlalchemy]` '
        'or install it directly with `pip install sqlalchemy`.'
    )
    raise ImportError(missing_dep_msg) from e  # pragma: no cover

from typing import Literal, TypeVar, overload

from odata_v4_query.errors import NoRootClassError
from odata_v4_query.query_parser import ODataQueryOptions

from ._func import compute_skip_from_page
from .filter_parsers.sql_filter_parser import (
    FilterType,
    SQLAlchemyFilterNodeParser,
)

T = TypeVar('T')
Query = Select[tuple[T, ...]]
ParsedQuery = Select[tuple[FilterType, ...]] | Select


@overload
def get_query_root_cls(
    query: Query[T],
    raise_on_none: Literal[True],
) -> type[T]: ...


@overload
def get_query_root_cls(
    query: Query[T],
    raise_on_none: bool = False,
) -> type[T] | None: ...


def get_query_root_cls(
    query: Query[T],
    raise_on_none: bool = False,
) -> type[T] | None:
    """Return the root class of a query.

    Returns the class of the first column of the query, this is:
    - When selecting specific columns, returns the class of
        the first column (the same for functions like ``count()``).
    - When selecting multiple classes, returns the class of
        the first class.
    - When joining, returns the class of the first table.

    Parameters
    ----------
    query : Query[T]
        SQLAlchemy query.
    raise_on_none : bool, optional
        If True, raises an error if no root class is found,
        by default False.

    Returns
    -------
    type[T] | None
        Root class of the query.

    Raises
    ------
    NoRootClassError
        If no root class is found and ``raise_on_none`` is True.

    Examples
    --------
    Usage:
    >>> query = select(User)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns:
    >>> query = select(User.id)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns with functions:
    >>> query = select(func.count(User.id))
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting multiple classes:
    >>> query = select(User, Post)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns from multiple classes:
    >>> query = select(User.id, Post.title)
    >>> get_query_root_cls(query)
    <class 'User'>

    Joining:
    >>> query = select(User).join(Post)
    >>> get_query_root_cls(query)
    <class 'User'>
    >>> query = select(Post).join(User)
    >>> get_query_root_cls(query)
    <class 'Post'>

    No root class found:
    >>> query = select(func.count('*'))
    >>> get_query_root_cls(query)
    None
    >>> get_query_root_cls(query, raise_on_none=True)
    Traceback (most recent call last):
        ...
    NoRootClassError: could not find root class of query: <...>

    """
    for col_desc in query.column_descriptions:
        entity = col_desc.get('entity')
        if entity is not None:
            return entity

    if raise_on_none:
        raise NoRootClassError(str(query))

    return None


@overload
def apply_to_sqlalchemy_query(
    options: ODataQueryOptions,
    model_or_query: type[FilterType],
    search_fields: list[str] | None = None,
) -> Select[tuple[FilterType, ...]]: ...


@overload
def apply_to_sqlalchemy_query(
    options: ODataQueryOptions,
    model_or_query: Select,
    search_fields: list[str] | None = None,
) -> Select: ...


def apply_to_sqlalchemy_query(  # noqa: C901, PLR0912
    options: ODataQueryOptions,
    model_or_query: type[FilterType] | Select,
    search_fields: list[str] | None = None,
) -> ParsedQuery:
    """Apply OData query options to a SQLAlchemy query.

    Parameters
    ----------
    options : ODataQueryOptions
        Parsed query options.
    model_or_query : type[FilterType] | Select
        SQLAlchemy model class or query to apply options to.
    search_fields : list[str] | None, optional
        Fields to search in if ``$search`` is used, by default None.

    Returns
    -------
    ParsedQuery
        SQLAlchemy query with applied options.

    Raises
    ------
    NoRootClassFound
        If the root class of the query cannot be found.

    Notes
    -----
    #### Pagination
    If ``$page`` option is provided, ``$skip`` is overwritten
    using ``odata_v4_query.utils.compute_skip_from_page()``.
    If ``$top`` is not provided, it defaults to
    ``odata_v4_query.definitions.DEFAULT_LIMIT``.

    #### Search
    The ``$search`` option is only supported if ``search_fields``
    is provided.

    #### Expand
    The ``$expand`` option performs a
    `joined eager loading <https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#sqlalchemy.orm.joinedload>`_
    using left outer join.

    #### Count
    If ``$count`` is provided, the query is returned with a
    ``count(*)`` column. The columns of the original query
    are discarded. Also, ``$orderby``, ``$expand`` and ``$select``
    are ignored.

    #### Unsupported options
    The ``$format`` option is not supported.

    Examples
    --------
    Assuming the following ``User`` SQLAlchemy model:
    >>> from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    >>> class User(DeclarativeBase):
    ...     name: Mapped[str] = mapped_column()
    ...     email: Mapped[str] = mapped_column()
    ...     age: Mapped[int] = mapped_column()

    Create a new query with applied options:
    >>> from odata_v4_query import ODataQueryParser
    >>> from odata_v4_query.utils.sqlalchemy import apply_to_sqlalchemy_query
    >>> parser = ODataQueryParser()
    >>> options = parser.parse_query_string('$top=10&$skip=20')
    >>> query = apply_to_sqlalchemy_query(options, User)

    Apply options to an existing query:
    >>> query = select(User)
    >>> query = apply_to_sqlalchemy_query(options, query)

    Apply ``$search`` option:
    >>> query = apply_to_sqlalchemy_query(
    ...     options,
    ...     User,
    ...     search_fields=['name', 'email']
    ... )
    >>> query = apply_to_sqlalchemy_query(
    ...     options,
    ...     select(User),
    ...     search_fields=['name', 'email']
    ... )

    """
    compute_skip_from_page(options)

    if isinstance(model_or_query, Select):
        query = model_or_query
        root_cls = get_query_root_cls(query)
    else:
        query = select(model_or_query)
        root_cls = model_or_query

    if options.skip:
        query = query.offset(options.skip)

    if options.top:
        query = query.limit(options.top)

    if options.filter_:
        if not root_cls:
            raise NoRootClassError(str(query), '$filter')

        parser = SQLAlchemyFilterNodeParser(root_cls)
        filters = parser.parse(options.filter_)
        query = query.where(filters)

    if options.search and search_fields:
        if not root_cls:
            raise NoRootClassError(str(query), '$search')

        query = query.where(
            or_(
                *[
                    getattr(root_cls, field).ilike(f'%{options.search}%')
                    for field in search_fields
                ],
            ),
        )

    if options.count:
        return query.with_only_columns(func.count('*'), maintain_column_froms=True)

    if options.orderby:
        if not root_cls:
            raise NoRootClassError(str(query), '$orderby')

        for item in options.orderby:
            if item.direction == 'asc':
                query = query.order_by(getattr(root_cls, item.field))
            else:
                query = query.order_by(getattr(root_cls, item.field).desc())

    if options.expand:
        if not root_cls:
            raise NoRootClassError(str(query), '$expand')

        for field in options.expand:
            query = query.options(joinedload(getattr(root_cls, field)))

    if options.select:
        if not root_cls:
            raise NoRootClassError(str(query), '$select')

        query = query.with_only_columns(
            *[getattr(root_cls, field) for field in options.select],
        )

    return query
