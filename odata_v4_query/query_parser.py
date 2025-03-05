from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from .errors import NoPositiveIntegerValue, UnsupportedFormat
from .filter_parser import (
    FilterNode,
    ODataFilterParser,
    ODataFilterParserProtocol,
)

OptionCallback = Callable[[str, 'ODataQueryOptions'], None]


@dataclass
class ODataQueryOptions:
    count: bool = False
    expand: list[str] | None = None
    filter_: FilterNode | None = None
    format_: str | None = None
    orderby: list[dict[str, str]] | None = None
    search: str | None = None
    select: list[str] | None = None
    skip: int | None = None
    top: int | None = None


class ODataQueryParser:
    """Parser for OData V4 query options supporting
    standard query parameters.
    """

    __supported_options: dict[str, OptionCallback]
    """Supported query options."""

    __supported_formats: Sequence[str]
    """Supported response formats."""

    __filter_parser: ODataFilterParserProtocol
    """Filter parser."""

    def __init__(
        self,
        supported_options: dict[str, OptionCallback] | None = None,
        supported_formats: Sequence[str] | None = None,
        filter_parser: ODataFilterParserProtocol | None = None,
    ) -> None:
        """Parser for OData V4 query options supporting
        standard query parameters.

        Parameters
        ----------
        supported_options : dict[str, OptionCallback] | None, optional
            Dictionary of supported query options, by default None.
        supported_formats : Sequence[str] | None, optional
            Sequence of supported response formats, by default None.
        filter_parser : ODataFilterParserProtocol | None, optional
            Filter parser, by default None.
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
        }

        self.__supported_formats = supported_formats or (
            'json',
            'xml',
            'csv',
            'tsv',
        )

        self.__filter_parser = filter_parser or ODataFilterParser()

    def set_supported_options(
        self, supported_options: dict[str, OptionCallback]
    ) -> None:
        """Sets the supported query options.

        Parameters
        ----------
        supported_options : dict[str, OptionCallback]
            Dictionary of supported query options.
        """
        self.__supported_options = supported_options

    def set_supported_formats(self, supported_formats: Sequence[str]) -> None:
        """Sets the supported response formats.

        Parameters
        ----------
        supported_formats : Sequence[str]
            Sequence of supported response formats.
        """
        self.__supported_formats = supported_formats

    def set_filter_parser(
        self, filter_parser: ODataFilterParserProtocol
    ) -> None:
        """Sets the filter parser.

        Parameters
        ----------
        filter_parser : ODataFilterParserProtocol
            Filter parser.
        """
        self.__filter_parser = filter_parser

    def parse_url(self, url: str) -> ODataQueryOptions:
        """Parses a complete OData URL and
        extracts query options.

        Parameters
        ----------
        url : str
            Complete OData URL including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
        """
        parsed_url = urlparse(url)
        return self.parse_query_string(parsed_url.query)

    def parse_query_string(self, query_string: str) -> ODataQueryOptions:
        """Parses a complete OData query string and
        extracts query options.

        Parameters
        ----------
        query_string : str
            Complete OData query string including query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
        """
        query_params = parse_qs(query_string)
        return self.parse_query_params(query_params)

    def parse_query_params(
        self, query_params: dict[str, list[str]]
    ) -> ODataQueryOptions:
        """Parses OData query parameters and returns structured options.

        Parameters
        ----------
        query_params : dict[str, list[str]]
            Dictionary of query parameters.

        Returns
        -------
        ODataQueryOptions
            Parsed parameters.
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

    def _parse_count(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $count parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.count = value.lower() == 'true'

    def _parse_expand(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $expand parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.expand = self._split_by_comma(value)

    def _parse_filter(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $filter parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.filter_ = self.__filter_parser.parse(value)

    def _parse_format(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $format parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        UnsupportedFormat
            If the format is not supported.
        """
        if value not in self.__supported_formats:
            raise UnsupportedFormat(value)

        options.format_ = value

    def _parse_orderby(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $orderby parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        orderby_list = []
        for item in value.split(','):
            item = item.strip()
            lowercased_item = item.lower()
            if lowercased_item.endswith(' asc'):
                field, direction = item.rsplit(' asc', 1)
            elif lowercased_item.endswith(' desc'):
                field, direction = item.rsplit(' desc', 1)
            else:
                field = item
                direction = 'asc'  # default direction

            orderby_list.append(
                {'field': field.strip(), 'direction': direction.strip()}
            )

        options.orderby = orderby_list

    def _parse_search(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $search parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.search = value.strip()

    def _parse_select(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $select parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.
        """
        options.select = self._split_by_comma(value)

    def _parse_skip(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $skip parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoPositiveIntegerValue
            If the value is not a positive integer.
        """
        try:
            options.skip = int(value)
            assert options.skip >= 0
        except (AssertionError, ValueError, TypeError):
            raise NoPositiveIntegerValue('$skip', value)

    def _parse_top(self, value: str, options: ODataQueryOptions) -> None:
        """Parses $top parameter.

        Parameters
        ----------
        value : str
            Value of the parameter.
        options : ODataQueryOptions
            Current query options object.

        Raises
        ------
        NoPositiveIntegerValue
            If the value is not a positive integer.
        """
        try:
            options.top = int(value)
            assert options.top >= 0
        except (AssertionError, ValueError, TypeError):
            raise NoPositiveIntegerValue('$top', value)

    def _split_by_comma(self, value: str) -> list[str]:
        """Splits a string by comma.

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
