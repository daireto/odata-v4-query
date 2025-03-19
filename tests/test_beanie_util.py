import pytest
import pytest_asyncio

from odata_v4_query.errors import ParseError, UnexpectedNullOperand
from odata_v4_query.filter_parser import FilterNode
from odata_v4_query.query_parser import ODataQueryOptions, ODataQueryParser
from odata_v4_query.utils.beanie import apply_to_beanie_query

from ._core.beanie import User, UserProjection, get_client, seed_data


@pytest_asyncio.fixture(autouse=True)
async def client():
    client = await get_client()
    await seed_data()
    return client


@pytest.mark.asyncio(loop_scope='session')
class TestBeanie:

    parser = ODataQueryParser()

    async def test_skip(self):
        users_count = len(await User.find().to_list())
        options = self.parser.parse_query_string('$skip=2')
        query = apply_to_beanie_query(options, User.find())
        result = await query.to_list()
        assert len(result) == users_count - 2
        assert result[0].name == 'Alice'

    async def test_top(self):
        options = self.parser.parse_query_string('$top=2')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'John'
        assert result[1].name == 'Jane'

    async def test_page(self):
        users_count = len(await User.find().to_list())

        # default top
        options = self.parser.parse_query_string('$page=1')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == users_count

        # top 3
        options = self.parser.parse_query_string('$page=1&$top=4')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 4
        options = self.parser.parse_query_string('$page=2&$top=4')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 4
        options = self.parser.parse_query_string('$page=3&$top=4')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        options = self.parser.parse_query_string('$page=4&$top=4')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 0

    async def test_filter(self):
        # comparison and logical
        options = self.parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 1
        assert result[0].name == 'John'

        options = self.parser.parse_query_string(
            '$filter=age lt 25 or age gt 35'
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 4

        options = self.parser.parse_query_string(
            "$filter=name in ('Eve', 'Frank')"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'Eve'
        assert result[1].name == 'Frank'

        options = self.parser.parse_query_string(
            "$filter=name nin ('Eve', 'Frank')"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 8

        options = self.parser.parse_query_string(
            "$filter=name ne 'John' and name ne 'Jane'"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 8

        options = self.parser.parse_query_string(
            "$filter=not name eq 'John' and not name eq 'Jane'"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 8

        options = self.parser.parse_query_string('$filter=name eq null')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 0

        options = self.parser.parse_query_string('$filter=name ne null')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 10

        # string functions
        options = self.parser.parse_query_string(
            "$filter=startswith(name, 'J') and age ge 25"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'John'
        assert result[1].name == 'Jane'

        options = self.parser.parse_query_string(
            "$filter=endswith(name, 'e')"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 5
        assert result[0].name == 'Jane'
        assert result[1].name == 'Alice'
        assert result[2].name == 'Charlie'
        assert result[3].name == 'Eve'
        assert result[4].name == 'Grace'

        options = self.parser.parse_query_string(
            "$filter=contains(name, 'i') and age le 35"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'Alice'
        assert result[0].age == 35
        assert result[1].name == 'Charlie'
        assert result[1].age == 32

        # collection
        options = self.parser.parse_query_string(
            "$filter=addresses has '101 Main St'"
        )
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'Alice'
        assert result[1].name == 'Bob'

    async def test_search(self):
        options = self.parser.parse_query_string('$search=John')
        query = apply_to_beanie_query(
            options, User, search_fields=['name', 'email']
        )
        result = await query.to_list()
        assert len(result) == 1
        assert result[0].name == 'John'

    async def test_orderby(self):
        options = self.parser.parse_query_string('$orderby=name asc,age desc')
        query = apply_to_beanie_query(options, User)
        result = await query.to_list()
        assert len(result) == 10
        assert result[0].name == 'Alice'
        assert result[1].name == 'Bob'
        assert result[1].age == 40
        assert result[2].name == 'Bob'
        assert result[2].age == 28
        assert result[3].name == 'Charlie'
        assert result[4].name == 'David'
        assert result[5].name == 'Eve'
        assert result[6].name == 'Frank'
        assert result[7].name == 'Grace'
        assert result[8].name == 'Jane'
        assert result[9].name == 'John'

    async def test_select(self):
        options = self.parser.parse_query_string('$select=name,email')
        query = apply_to_beanie_query(options, User, parse_select=True)
        result = await query.to_list()
        assert len(result) == 10
        assert result[0]['name'] == 'John'
        assert result[0]['email'] == 'john@example.com'

    async def test_projection(self):
        options = self.parser.parse_query_string('$top=1')
        query = apply_to_beanie_query(
            options, User, projection_model=UserProjection
        )
        result = await query.to_list()
        assert len(result) == 1
        assert isinstance(result[0], UserProjection)
        assert result[0].name == 'John'
        assert result[0].email == 'john@example.com'

        options = self.parser.parse_query_string('$top=1&$select=name,email')
        query = apply_to_beanie_query(
            options, User, projection_model=UserProjection, parse_select=True
        )
        result = await query.to_list()
        assert len(result) == 1
        assert isinstance(result[0], UserProjection)
        assert result[0].name == 'John'
        assert result[0].email == 'john@example.com'

    async def test_error(self):
        # unexpected null filters
        with pytest.raises(ParseError):
            options = ODataQueryOptions(filter_=FilterNode(type_='value'))
            apply_to_beanie_query(options, User)

        # null left or right operands
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='eq')
            )
            apply_to_beanie_query(options, User)

        # null left or right values
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='eq',
                    left=FilterNode(type_='identifier'),
                    right=FilterNode(type_='literal', value='John'),
                )
            )
            apply_to_beanie_query(options, User)

        # null list arguments
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='in',
                    left=FilterNode(type_='identifier', value='name'),
                    right=FilterNode(type_='list'),
                )
            )
            apply_to_beanie_query(options, User)

        # null operand for has operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='has',
                    left=FilterNode(type_='identifier', value='addresses'),
                    right=FilterNode(type_='literal'),
                )
            )
            apply_to_beanie_query(options, User)

        # null operand for and/or operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='and')
            )
            apply_to_beanie_query(options, User)

        # null operand for not/nor operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='not')
            )
            apply_to_beanie_query(options, User)

        # unknown operator
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='unknown')
            )
            apply_to_beanie_query(options, User)

        # null function
        with pytest.raises(ParseError):
            options = ODataQueryOptions(filter_=FilterNode(type_='function'))
            apply_to_beanie_query(options, User)

        # null function arguments
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='function', value='startswith')
            )
            apply_to_beanie_query(options, User)

        # more than 2 function arguments
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='function',
                    value='startswith',
                    arguments=[
                        FilterNode(type_='identifier', value='name'),
                        FilterNode(type_='literal', value='J'),
                        FilterNode(type_='literal', value='J'),
                    ],
                )
            )
            apply_to_beanie_query(options, User)

        # null function operand
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='function',
                    value='startswith',
                    arguments=[
                        FilterNode(type_='identifier', value='name'),
                        FilterNode(type_='literal'),
                    ],
                )
            )
            apply_to_beanie_query(options, User)

        # unknown function
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='function',
                    value='unknown',
                    arguments=[
                        FilterNode(type_='identifier', value='name'),
                        FilterNode(type_='literal', value='J'),
                    ],
                )
            )
            apply_to_beanie_query(options, User)
