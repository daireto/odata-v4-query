<p align="center">
    <img src="docs/images/logo.png" alt="OData V4 Query" />
</p>

<p align="center">
    <a href="https://pypi.org/project/odata-v4-query" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/odata-v4-query" alt="Supported Python versions">
    </a>
    <a href="https://pypi.org/project/odata-v4-query" target="_blank">
        <img src="https://img.shields.io/pypi/v/odata-v4-query" alt="Package version">
    </a>
    <a href="https://pypi.org/project/SQLAlchemy" target="_blank">
        <img src="https://img.shields.io/badge/SQLAlchemy-2.0%2B-orange" alt="Supported SQLAlchemy versions">
    </a>
    <a href="https://github.com/daireto/odata-v4-query/actions" target="_blank">
        <img src="https://github.com/daireto/odata-v4-query/actions/workflows/publish.yml/badge.svg" alt="Publish">
    </a>
    <a href='https://coveralls.io/github/daireto/odata-v4-query?branch=main'>
        <img src='https://coveralls.io/repos/github/daireto/odata-v4-query/badge.svg?branch=main' alt='Coverage Status' />
    </a>
    <a href="/LICENSE" target="_blank">
        <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
    </a>
</p>

<!-- omit in toc -->
# OData V4 Query

A lightweight, simple and fast parser for OData V4 query options supporting
standard query parameters. Provides helper functions to apply OData V4 query
options to ORM/ODM queries such as SQLAlchemy and Beanie, and SQLAlchemy
wrappers such as OData V4 Query.

Visit the [documentation website](https://daireto.github.io/odata-v4-query/).

<!-- omit in toc -->
## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
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
    - Comparison operators: `eq`, `ne`, `gt`, `ge`, `lt`, `le`
    - Logical operators: `and`, `or`, `not`
    - Collection operators: `in`, `has`
    - String functions: `startswith`, `endswith`, `contains`

- Utility functions to apply query options to SQLAlchemy, Beanie and
  SQLActive queries.

## Requirements

Python>=3.10

Optional dependencies:
- beanie>=1.29.0 (for Beanie ODM support)
- sqlactive>=0.3.0 (for SQLActive support)
- sqlalchemy>=2.0.0 (for SQLAlchemy support)

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
options = parser.parse_query_string('$filter=name eq \'John\' and age gt 25')

# Parse filter expressions
filter_parser = ODataFilterParser()
ast = filter_parser.parse('name eq \'John\' and age gt 25')
```

## Documentation

Find the complete documentation [here](https://daireto.github.io/sqlactive/).

## Contributing

Please read the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Support

If you find this project useful, give it a ⭐ on GitHub to show your support!
