import pytest
import pytest_asyncio

from odata_v4_query.query_parser import ODataQueryParser
from odata_v4_query.utils import apply_to_beanie_query

from ._core import User, UserProjection, get_client, seed_data


@pytest_asyncio.fixture
async def client():
    client = await get_client()
    await seed_data()
    yield client
    client.close()


@pytest.mark.asyncio(loop_scope='session')
class TestBeanie:

    async def test_beanie(self, client):
        parser = ODataQueryParser()

        options = parser.parse_query_string(
            '$top=3&$skip=2&$orderby=name asc,email desc'
        )
        query = apply_to_beanie_query(User.find(), options)
        result = await query.to_list()
        assert len(result) == 3
        assert result[0].name == 'Bobby'
        assert result[1].name == 'Charlie'
        assert result[2].name == 'David'

        options = parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25&$select=name,email"
        )
        query = apply_to_beanie_query(User, options, parse_select=True)
        result = await query.to_list()
        assert len(result) == 1
        assert result[0]['name'] == 'John'
        assert result[0]['email'] == 'john@example.com'

        options = parser.parse_query_string('$search=John&$select=name,email')
        query = apply_to_beanie_query(
            User,
            options,
            projection_model=UserProjection,
            parse_select=True,
            search_fields=['name', 'email'],
        )
        result = await query.to_list()
        assert len(result) == 1
        assert result[0].name == 'John'
        assert result[0].email == 'john@example.com'
