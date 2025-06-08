import pytest

from odata_v4_query.errors import InvalidNumberError, TokenizeError
from odata_v4_query.filter_tokenizer import ODataFilterTokenizer


class TestFilterTokenizer:
    tokenizer = ODataFilterTokenizer()

    def test_tokenize(self):
        tokens1 = self.tokenizer.tokenize("name eq 'John' and age gt 25")
        tokens2 = self.tokenizer.tokenize('name eq "John" and age gt 25')
        tokens3 = self.tokenizer.tokenize("name eq 'D\\'Angelo' and age gt 25")
        tokens4 = self.tokenizer.tokenize("name eq 'D\\")
        tokens5 = self.tokenizer.tokenize(
            "name eq 'John' or startswith(name, 'J') and age gt 25 or age in (25, 30)"
        )
        assert len(tokens1) == 7
        assert len(tokens2) == 7
        assert len(tokens3) == 7
        assert len(tokens4) == 3
        assert len(tokens5) == 22

    def test_invalid_character(self):
        with pytest.raises(TokenizeError):
            self.tokenizer.tokenize("name eq 'John' and age gt #")

    def test_invalid_number(self):
        with pytest.raises(InvalidNumberError):
            self.tokenizer.tokenize("name eq 'John' and age gt 25d")

    def test_invalid_number_with_more_than_one_decimal_point(self):
        with pytest.raises(InvalidNumberError):
            self.tokenizer.tokenize("name eq 'John' and age gt 24..0")
