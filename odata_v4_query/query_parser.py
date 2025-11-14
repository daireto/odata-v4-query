import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlparse

from .definitions import DEFAULT_FORMAT_OPTIONS, DEFAULT_ORDERBY_DIRECTION
from .errors import (
    InvalidOrderDirectionError,
    NoNumericValueError,
    NoPositiveError,
    UnsupportedFormatError,
)
from .filter_parser import (
    FilterNode,
    ODataFilterParser,
    ODataFilterParserProtocol,
)

OptionCallback = Callable[[str, 'ODataQueryOptions'], None]


@dataclass
class OrderbyItem:
    field: str
    direction: Literal['asc', 'desc']


@dataclass
class ODataQueryOptions:
    count: bool = False
    expand: list[str] | None = None
    filter_: FilterNode | None = None
    format_: str | None = None
    orderby: list[OrderbyItem] | None = None
    search: str | None = None
    select: list[str] | None = None
    skip: int | None = None
    top: int | None = None
    page: int | None = None

    def clone(self, deep: bool = False) -> 'ODataQueryOptions':
        """Clone the query options.

        Parameters
        ----------
        deep : bool, optional
            Whether to perform a deep copy using ``copy.deepcopy()``,
            by default nested objects (expand, filter_, orderby, select)
            are copied shallowly. **Use with caution:** Deep copying large
            lists and ASTs can be very expensive, and lead to high overhead.

        Returns
        -------
        ODataQueryOptions
            Cloned query options.

        """
        return ODataQueryOptions(
            count=self.count,
            expand=copy.deepcopy(self.expand) if deep else self.expand,
            filter_=copy.deepcopy(self.filter_) if deep else self.filter_,
            format_=self.format_,
            orderby=copy.deepcopy(self.orderby) if deep else self.orderby,
            search=self.search,
            select=copy.deepcopy(self.select) if deep else self.select,
            skip=self.skip,
            top=self.top,
            page=self.page,
        )


class ODataQueryParser:
    """Parser for standard OData V4 query options."""

    __supported_options: dict[str, OptionCallback]
    __supported_formats: Sequence[str]
    __filter_parser: ODataFilterParserProtocol

    def __init__(
        self,
        supported_options: dict[str, OptionCallback] | None = None,
        supported_formats: Sequence[str] | None = None,
        filter_parser: ODataFilterParserProtocol | None = None,
    ) -> None:
        """Initialize the query parser.

        Parameters
        ----------
        supported_options : dict[str, OptionCallback] | None, optional
            Dictionary of supported query options, by default None.
        supported_formats : Sequence[str] | None, optional
            Sequence of supported response formats, by default None.
        filter_parser : ODataFilterParserProtocol | None, optional
            Filter parser, by default, it uses an instance
            of ``ODataFilterParser``.

        """
        self.__supported_options = supported_options or {
            '$count': self._parse_count,
            '$expand': self._parse_expand,
            '$filter': self._parse_filter,
            '$format': self._parse_format,
            '$orderby': self._parse_orderby,
            '$search': self._parse_search,
            '$select': self._parse_select,
            '$skip': self._parse_skip,
            '$top': self._parse_top,
            '$page': self._parse_page,
        }
        self.__supported_formats = supported_formats or DEFAULT_FORMAT_OPTIONS
        self.__filter_parser = filter_parser or ODataFilterParser()

    def set_supported_options(
        self,
        supported_options: dict[str, OptionCallback],
    ) -> None:
        """Set the supported query options.

        Parameters
        ----------
        supported_options : dict[str, OptionCallback]
            Dictionary of supported query options.

        """
        self.__supported_options = supported_options  # pragma: no cover

    def set_supported_formats(self, supported_formats: Sequence[str]) -> None:
        """Set the supported response formats.

        Parameters
        ----------
        supported_formats : Sequence[str]
            Sequence of supported response formats.

        """
        self.__supported_formats = supported_formats  # pragma: no cover

    def set_filter_parser(
        self,
        filter_parser: ODataFilterParserProtocol,
    ) -> None:
        """Set the filter parser.

        Parameters
        ----------
        filter_parser : ODataFilterParserProtocol
            Filter parser.

        """
        self.__filter_parser = filter_parser  # pragma: no cover

    def parse_url(self, url: str) -> ODataQueryOptions:
        """Parse a complete OData URL and extracts query options.

        Parameters
        ----------
        url : str
            Complete OData URL including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.

        Examples
        --------
        >>> from odata_v4_query import ODataQueryParser
        >>> parser = ODataQueryParser()
        >>> url = 'https://example.com/odata?$count=true&$top=10&$skip=20'
        >>> options = parser.parse_url(url)
        >>> options.count
        True
        >>> options.top
        10
        >>> options.skip
        20

        """
        parsed_url = urlparse(url)
        return self.parse_query_string(parsed_url.query)

    def parse_query_string(self, query_string: str) -> ODataQueryOptions:
        """Parse a complete OData query string and extracts query options.

        Parameters
        ----------
        query_string : str
            Complete OData query string including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.

        Examples
        --------
        >>> from odata_v4_query import ODataQueryParser
        >>> parser = ODataQueryParser()
        >>> query_string = '$count=true&$top=10&$skip=20'
        >>> options = parser.parse_query_string(query_string)
        >>> options.count
        True
        >>> options.top
        10
        >>> options.skip
        20

        """
        query_params = parse_qs(query_string)
        return self.parse_query_params(query_params)

    def parse_query_params(
        self,
        query_params: dict[str, list[str]],
    ) -> ODataQueryOptions:
        """Parse OData query parameters and returns structured options.

        Parameters
        ----------
        query_params : dict[str, list[str]]
            Dictionary of query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.

        Examples
        --------
        >>> from odata_v4_query import ODataQueryParser
        >>> parser = ODataQueryParser()
        >>> query_params = {'$count': ['true'], '$top': ['10'], '$skip': ['20']}
        >>> options = parser.parse_query_params(query_params)
        >>> options.count
        True
        >>> options.top
        10
        >>> options.skip
        20

        """
        options = ODataQueryOptions()

        for param, values in query_params.items():
            if param in self.__supported_options:
                # get the first value since OData parameters shouldn't
                # have multiple values
                value = values[0] if values else None
                if not value:
                    continue

                parser_func = self.__supported_options[param]
                parser_func(value, options)

        return options

    def evaluate(
        self,
        options_or_filter: ODataQueryOptions | FilterNode,
    ) -> str:
        """Evaluate an AST to the original filter expression.

        Parameters
        ----------
        options_or_filter : ODataQueryOptions | FilterNode
            Parsed query options or filter AST.

        Returns
        -------
        str
            Filter expression.

        Examples
        --------
        >>> from odata_v4_query import ODataQueryParser
        >>> parser = ODataQueryParser()
        >>> query_string = "$filter=name eq 'John' and age gt 25"
        >>> ast = parser.parse_query_string(query_string)
        >>> parser.evaluate(ast)
        "name eq 'John' and age gt 25"

        """
        if isinstance(options_or_filter, FilterNode):
            return self.__filter_parser.evaluate(options_or_filter)

        if options_or_filter.filter_:
            return self.__filter_parser.evaluate(options_or_filter.filter_)

        return ''

    def _parse_count(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $count parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        options.count = value.lower() == 'true'

    def _parse_expand(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $expand parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        options.expand = self._split_by_comma(value)

    def _parse_filter(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $filter parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        options.filter_ = self.__filter_parser.parse(value)

    def _parse_format(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $format parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        UnsupportedFormatError
            If the format is not supported.

        """
        if value not in self.__supported_formats:
            raise UnsupportedFormatError(value)

        options.format_ = value

    def _parse_orderby(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $orderby parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        orderby_list = []
        for item in value.split(','):
            item_and_direction = item.strip()
            if not item_and_direction:
                continue

            if ' ' in item_and_direction:
                field, direction = item_and_direction.rsplit(maxsplit=1)
            else:
                field, direction = item_and_direction, DEFAULT_ORDERBY_DIRECTION

            direction = direction.lower()
            if direction not in ('asc', 'desc'):
                raise InvalidOrderDirectionError(direction)

            orderby_list.append(
                OrderbyItem(
                    field=field.strip(),
                    direction=direction.strip(),  # type: ignore
                ),
            )

        options.orderby = orderby_list

    def _parse_search(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $search parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        options.search = value.strip()

    def _parse_select(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $select parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        """
        options.select = self._split_by_comma(value)

    def _parse_skip(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $skip parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoNumericValueError
            If the value is not a number.
        NoPositiveError
            If the value is not a positive integer.

        """
        try:
            options.skip = int(value)
        except (ValueError, TypeError) as e:
            raise NoNumericValueError(value) from e

        if options.skip < 0:
            raise NoPositiveError(param='$skip', value=value)

    def _parse_top(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $top parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoNumericValueError
            If the value is not a number.
        NoPositiveError
            If the value is not a positive integer.

        """
        try:
            options.top = int(value)
        except (ValueError, TypeError) as e:
            raise NoNumericValueError(value) from e

        if options.top < 0:
            raise NoPositiveError(param='$top', value=value)

    def _parse_page(self, value: str, options: ODataQueryOptions) -> None:
        """Parse $page parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoNumericValueError
            If the value is not a number.
        NoPositiveError
            If the value is not a positive integer.

        """
        try:
            options.page = int(value)
        except (ValueError, TypeError) as e:
            raise NoNumericValueError(value) from e

        if options.page < 0:
            raise NoPositiveError(param='$page', value=value)

    def _split_by_comma(self, value: str) -> list[str]:
        """Split a string by comma.

        Parameters
        ----------
        value : str
            String to be split.

        Returns
        -------
        list[str]
            List of strings.

        """
        return [item.strip() for item in value.split(',')]
