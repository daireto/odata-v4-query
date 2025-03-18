<!-- omit in toc -->
# OData V4 Query

A lightweight, simple and fast parser for OData V4 query options supporting
standard query parameters. Provides helper functions to apply OData V4 query
options to ORM/ODM queries such as SQLAlchemy and Beanie, and SQLAlchemy
wrappers such as SQLActive.

<!-- omit in toc -->
## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

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
    - Comparison operators: `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `in`, `nin`
    - Logical operators: `and`, `or`, `not`, `nor`
    - Collection operators: `has`
    - String functions: `startswith`, `endswith`, `contains`

- Utility functions to apply query options to SQLAlchemy, Beanie and
  SQLActive queries.

## Requirements

- `Python>=3.10`
- `beanie>=1.23.0 (optional, for Beanie ODM support)`
- `sqlactive>=0.3.0 (optional, for SQLActive support)`
- `sqlalchemy>=2.0.0 (optional, for SQLAlchemy support)`

## Installation

You can simply install odata-v4-query from
[PyPI](https://pypi.org/project/odata-v4-query/):
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
options = parser.parse_query_string("$filter=name eq 'John' and age gt 25")

# Parse filter expressions
filter_parser = ODataFilterParser()
ast = filter_parser.parse("name eq 'John' and age gt 25")

# Evaluate filter expressions
filter_parser.evaluate(ast)
```

## Contributing

See the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE)
file for details.

## Support

If you find this project useful, give it a ⭐ on GitHub!
