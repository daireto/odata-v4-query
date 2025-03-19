import pytest

from odata_v4_query.errors import NoPositiveIntegerValue, UnsupportedFormat
from odata_v4_query.query_parser import ODataQueryParser


class TestODataQueryParser:

    parser = ODataQueryParser()

    def test_parse_url(self):
        url = 'https://example.com/odata?$count=true&$top=10&$skip=20'
        options = self.parser.parse_url(url)
        assert options.count
        assert options.top == 10
        assert options.skip == 20

    def test_parse_query_string(self):
        query_string = '$count=true&$top=10&$skip=20'
        options = self.parser.parse_query_string(query_string)
        assert options.count
        assert options.top == 10
        assert options.skip == 20

    def test_parse_query_params(self):
        query_params = {
            '$count': ['true'],
            '$top': ['10'],
            '$skip': ['20'],
            '$format': None,
        }
        options = self.parser.parse_query_params(query_params)
        assert options.count
        assert options.top == 10
        assert options.skip == 20
        assert options.format_ is None

    def test_parse_count(self):
        options = self.parser.parse_query_string('$count=true')
        assert options.count is True

        options = self.parser.parse_query_string('$count=false')
        assert options.count is False

    def test_parse_expand(self):
        options = self.parser.parse_query_string('$expand=field1,field2')
        assert options.expand == ['field1', 'field2']

    def test_parse_filter_and_evaluate(self):
        query_string = "$filter=name eq 'John' and age gt 25"
        options = self.parser.parse_query_string(query_string)
        assert options.filter_ is not None

        EXPECTED = "name eq 'John' and age gt 25"
        assert self.parser.evaluate(options) == EXPECTED
        assert self.parser.evaluate(options.filter_) == EXPECTED

        options.filter_ = None
        assert self.parser.evaluate(options) == ''

    def test_parse_format(self):
        options = self.parser.parse_query_string('$format=json')
        assert options.format_ == 'json'

    def test_parse_orderby(self):
        options = self.parser.parse_query_string(
            '$orderby=name asc,age desc,,email'
        )
        assert options.orderby is not None
        assert options.orderby[0].field == 'name'
        assert options.orderby[0].direction == 'asc'
        assert options.orderby[1].field == 'age'
        assert options.orderby[1].direction == 'desc'
        assert options.orderby[2].field == 'email'
        assert options.orderby[2].direction == 'asc'

    def test_parse_search(self):
        options = self.parser.parse_query_string('$search=John')
        assert options.search == 'John'

    def test_parse_select(self):
        options = self.parser.parse_query_string('$select=name,email')
        assert options.select == ['name', 'email']

    def test_parse_skip(self):
        options = self.parser.parse_query_string('$skip=10')
        assert options.skip == 10

    def test_parse_top(self):
        options = self.parser.parse_query_string('$top=10')
        assert options.top == 10

    def test_parse_page(self):
        options = self.parser.parse_query_string('$page=10')
        assert options.page == 10

    def test_parse_error(self):
        # unsupported format
        with pytest.raises(UnsupportedFormat):
            self.parser.parse_query_string('$format=html')

        # invalid skip
        with pytest.raises(NoPositiveIntegerValue):
            self.parser.parse_query_string('$skip=-10')

        # invalid top
        with pytest.raises(NoPositiveIntegerValue):
            self.parser.parse_query_string('$top=-10')

        # invalid page
        with pytest.raises(NoPositiveIntegerValue):
            self.parser.parse_query_string('$page=-10')
