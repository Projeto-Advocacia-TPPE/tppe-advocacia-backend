from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest


def make_request(base="http://testserver"):
    request = MagicMock()

    def url_for(name, **kwargs):
        article_id = kwargs.get("article_id", "")
        if name == "get_article":
            return f"{base}/api/v1/articles/{article_id}"
        if name == "preview_article":
            return f"{base}/api/v1/articles/{article_id}/preview"
        return ""

    request.url_for.side_effect = url_for
    return request

from app.modules.articles.model import ArticleStatus
from app.modules.articles.schema import ArticleCreate, ArticleUpdate
from app.modules.articles.service import ArticleService
from app.modules.users.model import Role
from app.shared.exceptions import ArticleNotFoundError


def make_author(**kwargs):
    defaults = {"id": 1, "name": "Dr. Silva", "role": Role.USER}
    defaults.update(kwargs)
    author = MagicMock()
    for key, value in defaults.items():
        setattr(author, key, value)
    return author


def make_article(**kwargs):
    now = datetime.now(UTC)
    defaults = {
        "id": 1,
        "title": "Artigo Teste",
        "content": "Conteúdo do artigo",
        "category": "Direito Civil",
        "summary": None,
        "cover_image_url": None,
        "status": ArticleStatus.DRAFT,
        "author_id": 1,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    author = make_author(id=defaults["author_id"])
    article = MagicMock()
    for key, value in defaults.items():
        setattr(article, key, value)
    article.author = author
    return article


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    svc = ArticleService.__new__(ArticleService)
    svc.repository = repo
    return svc


class TestCreate:
    def test_returns_article_read_on_success(self, service, repo):
        repo.create.return_value = make_article(id=1, title="Novo Artigo")

        result = service.create(
            ArticleCreate(title="Novo Artigo", content="Conteúdo", category="Civil", summary="Resumo do artigo"),
            author=make_author(id=1),
        )

        assert result.id == 1
        assert result.title == "Novo Artigo"

    def test_default_status_is_draft(self, service, repo):
        repo.create.return_value = make_article(status=ArticleStatus.DRAFT)

        service.create(
            ArticleCreate(title="T", content="C", category="Cat", summary="Resumo do artigo"),
            author=make_author(),
        )

        assert repo.create.call_args.kwargs["status"] == ArticleStatus.DRAFT

    def test_passes_author_id_to_repo(self, service, repo):
        repo.create.return_value = make_article(author_id=5)

        service.create(
            ArticleCreate(title="T", content="C", category="Cat", summary="Resumo do artigo"),
            author=make_author(id=5),
        )

        assert repo.create.call_args.kwargs["author_id"] == 5

    def test_author_name_in_result(self, service, repo):
        repo.create.return_value = make_article()

        result = service.create(
            ArticleCreate(title="T", content="C", category="Cat", summary="Resumo do artigo"),
            author=make_author(name="Dr. Silva"),
        )

        assert result.author_name == "Dr. Silva"


class TestUpdate:
    def test_raises_article_not_found_when_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ArticleNotFoundError):
            service.update(999, ArticleUpdate(title="Novo"))

    def test_does_not_call_repo_update_when_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ArticleNotFoundError):
            service.update(999, ArticleUpdate(title="Novo"))

        repo.update.assert_not_called()

    def test_passes_only_non_none_fields(self, service, repo):
        article = make_article()
        repo.get_by_id.return_value = article
        repo.update.return_value = article

        service.update(1, ArticleUpdate(title="Novo Título"))

        data = repo.update.call_args[0][1]
        assert "title" in data
        assert "content" not in data
        assert "category" not in data

    def test_returns_updated_article_read(self, service, repo):
        repo.get_by_id.return_value = make_article()
        repo.update.return_value = make_article(title="Atualizado")

        result = service.update(1, ArticleUpdate(title="Atualizado"))

        assert result.title == "Atualizado"

    def test_can_publish_draft(self, service, repo):
        repo.get_by_id.return_value = make_article(status=ArticleStatus.DRAFT)
        repo.update.return_value = make_article(status=ArticleStatus.PUBLISHED)

        result = service.update(1, ArticleUpdate(status=ArticleStatus.PUBLISHED))

        assert result.status == ArticleStatus.PUBLISHED


class TestGetPublishedById:
    def test_returns_published_article(self, service, repo):
        repo.get_by_id.return_value = make_article(status=ArticleStatus.PUBLISHED)

        result = service.get_published_by_id(1)

        assert result.status == ArticleStatus.PUBLISHED

    def test_raises_when_article_not_found(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ArticleNotFoundError):
            service.get_published_by_id(999)

    def test_raises_when_article_is_draft(self, service, repo):
        repo.get_by_id.return_value = make_article(status=ArticleStatus.DRAFT)

        with pytest.raises(ArticleNotFoundError):
            service.get_published_by_id(1)


class TestGetPreview:
    def test_raises_article_not_found_when_missing(self, service, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(ArticleNotFoundError):
            service.get_preview(999)

    def test_returns_draft_article(self, service, repo):
        repo.get_by_id.return_value = make_article(status=ArticleStatus.DRAFT)

        result = service.get_preview(1)

        assert result.status == ArticleStatus.DRAFT

    def test_returns_published_article(self, service, repo):
        repo.get_by_id.return_value = make_article(status=ArticleStatus.PUBLISHED)

        result = service.get_preview(1)

        assert result.status == ArticleStatus.PUBLISHED


class TestListPublished:
    def test_returns_empty_list_when_none(self, service, repo):
        repo.get_published.return_value = ([], 0)

        result, total = service.list_published(make_request())

        assert result == []
        assert total == 0

    def test_returns_only_published(self, service, repo):
        repo.get_published.return_value = (
            [
                make_article(id=1, status=ArticleStatus.PUBLISHED),
                make_article(id=2, status=ArticleStatus.PUBLISHED),
            ],
            2,
        )

        result, total = service.list_published(make_request())

        assert len(result) == 2
        assert total == 2

    def test_url_points_to_article(self, service, repo):
        repo.get_published.return_value = ([make_article(id=42)], 1)

        result, _ = service.list_published(make_request())

        assert result[0].url == "http://testserver/api/v1/articles/42"

    def test_returns_list_item_fields(self, service, repo):
        repo.get_published.return_value = ([make_article(id=1, title="Título")], 1)

        result, _ = service.list_published(make_request())

        item = result[0]
        assert item.id == 1
        assert item.title == "Título"
        assert hasattr(item, "summary")
        assert hasattr(item, "created_at")
        assert hasattr(item, "url")
        assert hasattr(item, "status")


class TestListAll:
    def test_returns_empty_list_when_none(self, service, repo):
        repo.get_all.return_value = ([], 0)

        result, total = service.list_all(make_request())

        assert result == []
        assert total == 0

    def test_returns_all_articles_including_drafts(self, service, repo):
        repo.get_all.return_value = (
            [
                make_article(id=1, status=ArticleStatus.DRAFT),
                make_article(id=2, status=ArticleStatus.PUBLISHED),
            ],
            2,
        )

        result, total = service.list_all(make_request())

        assert len(result) == 2
        assert total == 2

    def test_url_points_to_preview(self, service, repo):
        repo.get_all.return_value = ([make_article(id=7)], 1)

        result, _ = service.list_all(make_request())

        assert result[0].url == "http://testserver/api/v1/articles/7/preview"

    def test_returns_status_in_list_item(self, service, repo):
        repo.get_all.return_value = ([make_article(id=1, status=ArticleStatus.DRAFT)], 1)

        result, _ = service.list_all(make_request())

        assert result[0].status == ArticleStatus.DRAFT
