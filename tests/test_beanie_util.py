import pytest
import pytest_asyncio

from odata_v4_query.query_parser import ODataQueryParser
from odata_v4_query.utils import apply_to_beanie_query

from ._core import User, UserProjection, get_client, seed_data


@pytest_asyncio.fixture(autouse=True)
async def client():
    client = await get_client()
    await seed_data()
    yield client
    client.close()


@pytest.mark.asyncio(loop_scope='session')
class TestBeanie:

    parser = ODataQueryParser()

    async def test_skip(self):
        users_count = len(await User.find().to_list())

        options = self.parser.parse_query_string('$skip=2')
        query = apply_to_beanie_query(User.find(), options)
        result = await query.to_list()
        assert len(result) == users_count - 2
        assert result[0].name == 'Alice'

    async def test_top(self):
        options = self.parser.parse_query_string('$top=2')
        query = apply_to_beanie_query(User, options)
        result = await query.to_list()
        assert len(result) == 2
        assert result[0].name == 'John'
        assert result[1].name == 'Jane'

    async def test_filter(self):
        options = self.parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25"
        )
        query = apply_to_beanie_query(User, options)
        result = await query.to_list()
        assert len(result) == 1
        assert result[0].name == 'John'

    async def test_search(self):
        options = self.parser.parse_query_string('$search=John')
        query = apply_to_beanie_query(
            User, options, search_fields=['name', 'email']
        )
        result = await query.to_list()
        assert len(result) == 1
        assert result[0].name == 'John'

    async def test_orderby(self):
        options = self.parser.parse_query_string('$orderby=name asc,age desc')
        query = apply_to_beanie_query(User, options)
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
        query = apply_to_beanie_query(User, options, parse_select=True)
        result = await query.to_list()
        assert len(result) == 10
        assert result[0]['name'] == 'John'
        assert result[0]['email'] == 'john@example.com'

    async def test_projection(self):
        options = self.parser.parse_query_string('$top=1')
        query = apply_to_beanie_query(
            User, options, projection_model=UserProjection
        )
        result = await query.to_list()
        assert len(result) == 1
        assert isinstance(result[0], UserProjection)
        assert result[0].name == 'John'
        assert result[0].email == 'john@example.com'

        options = self.parser.parse_query_string('$top=1&$select=name,email')
        query = apply_to_beanie_query(
            User, options, projection_model=UserProjection, parse_select=True
        )
        result = await query.to_list()
        assert len(result) == 1
        assert isinstance(result[0], UserProjection)
        assert result[0].name == 'John'
        assert result[0].email == 'john@example.com'
