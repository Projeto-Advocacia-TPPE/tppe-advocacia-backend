from app.utils.responses import paginated


class TestPaginated:
    def test_zero_total_returns_one_page(self):
        result = paginated([], total=0, page=1, limit=10)

        assert result.meta.pages == 1

    def test_total_exactly_one_limit_returns_one_page(self):
        result = paginated([], total=10, page=1, limit=10)

        assert result.meta.pages == 1

    def test_total_divisible_by_limit(self):
        result = paginated([], total=20, page=1, limit=10)

        assert result.meta.pages == 2

    def test_total_not_divisible_rounds_up(self):
        result = paginated([], total=21, page=1, limit=10)

        assert result.meta.pages == 3

    def test_total_less_than_limit_returns_one_page(self):
        result = paginated([], total=5, page=1, limit=10)

        assert result.meta.pages == 1

    def test_single_item_returns_one_page(self):
        result = paginated([], total=1, page=1, limit=10)

        assert result.meta.pages == 1

    def test_meta_carries_total(self):
        result = paginated([], total=42, page=1, limit=10)

        assert result.meta.total == 42

    def test_meta_carries_page(self):
        result = paginated([], total=100, page=3, limit=10)

        assert result.meta.page == 3

    def test_meta_carries_limit(self):
        result = paginated([], total=100, page=1, limit=25)

        assert result.meta.limit == 25

    def test_success_is_true(self):
        result = paginated([], total=0, page=1, limit=10)

        assert result.success is True

    def test_data_matches_items(self):
        items = [1, 2, 3]
        result = paginated(items, total=3, page=1, limit=10)

        assert result.data == items

    def test_empty_data_when_no_items(self):
        result = paginated([], total=0, page=1, limit=10)

        assert result.data == []
