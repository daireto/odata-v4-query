# OData V4 Query

A lightweight, simple and fast parser for OData V4 query options supporting
standard query parameters. This library provides helper functions to apply
OData V4 query options to ORM/ODM queries such as SQLAlchemy and Beanie, and
SQLAlchemy wrappers such as SQLActive.

## Features

- Full support for OData V4 standard query parameters:
  - `$count` - Include count of items
  - `$expand` - Expand related entities
  - `$filter` - Filter results
  - `$format` - Response format (json, xml, csv, tsv)
  - `$orderby` - Sort results
  - `$search` - Search items
  - `$select` - Select specific fields
  - `$skip` - Skip N items
  - `$top` - Limit to N items

- Comprehensive filter expression support:
  - Comparison operators: `eq`, `ne`, `gt`, `ge`, `lt`, `le`
  - Logical operators: `and`, `or`, `not`
  - Collection operators: `in`, `has`
  - String functions: `startswith`, `endswith`, `contains`

## Installation

```bash
pip install odata-v4-query
```

## Quick Start

```python
from odata_v4_query import ODataQueryParser, ODataFilterParser

# Create parser instance
parser = ODataQueryParser()

# Parse a complete URL
options = parser.parse_url('https://example.com/odata?$count=true&$top=10&$skip=20')

# Parse just the query string
options = parser.parse_query_string('$filter=name eq \'John\' and age gt 25')

# Parse filter expressions
filter_parser = ODataFilterParser()
ast = filter_parser.parse('name eq \'John\' and age gt 25')
```

## Requirements

- Python 3.7+
- beanie>=1.29.0 (optional, for Beanie ODM support)
- sqlactive>=0.3.1 (optional, for SQLActive support)
- sqlalchemy>=2.0.36 (optional, for SQLAlchemy support)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
