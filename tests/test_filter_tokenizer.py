import pytest

from odata_v4_query.errors import InvalidNumberError, TokenizeError
from odata_v4_query.filter_tokenizer import ODataFilterTokenizer


class TestFilterTokenizer:

    tokenizer = ODataFilterTokenizer()

    def test_tokenize(self):
        tokens = self.tokenizer.tokenize("name eq 'John' and age gt 25")
        assert len(tokens) == 7

        tokens = self.tokenizer.tokenize('name eq "John" and age gt 25')
        assert len(tokens) == 7

        tokens = self.tokenizer.tokenize("name eq 'D\\'Angelo' and age gt 25")
        assert len(tokens) == 7

        tokens = self.tokenizer.tokenize("name eq 'D\\")
        assert len(tokens) == 3

        tokens = self.tokenizer.tokenize(
            "name eq 'John' or startswith(name, 'J') and age gt 25 or age in (25, 30)"
        )
        assert len(tokens) == 22

    def test_tokenize_error(self):
        # invalid character
        with pytest.raises(TokenizeError):
            self.tokenizer.tokenize("name eq 'John' and age gt #")

        # invalid number
        with pytest.raises(InvalidNumberError):
            self.tokenizer.tokenize("name eq 'John' and age gt 25d")

        # number with multiple decimal points
        with pytest.raises(InvalidNumberError):
            self.tokenizer.tokenize("name eq 'John' and age gt 24..0")
