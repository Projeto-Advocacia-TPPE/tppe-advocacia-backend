import bcrypt
from sqlalchemy.orm import Session

from app.modules.articles.model import ArticleStatus
from app.modules.articles.repository import ArticleRepository
from app.modules.users.model import Role
from app.modules.users.repository import UserRepository


def make_user(db: Session, *, email="author@test.com"):
    return UserRepository(db).create(
        name="Dr. Silva",
        email=email,
        hashed_password=bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode(),
        role=Role.USER,
    )


def make_article(repo: ArticleRepository, author_id: int, **kwargs):
    defaults = {
        "title": "Artigo Teste",
        "content": "Conteúdo",
        "category": "Direito Civil",
        "author_id": author_id,
        "cover_image_url": None,
        "status": ArticleStatus.DRAFT,
    }
    defaults.update(kwargs)
    return repo.create(**defaults)


class TestCreate:
    def test_persists_article_with_correct_fields(self, db: Session):
        user = make_user(db)
        repo = ArticleRepository(db)

        article = make_article(
            repo, user.id, title="Meu Artigo", category="Trabalhista"
        )

        assert article.id is not None
        assert article.title == "Meu Artigo"
        assert article.category == "Trabalhista"
        assert article.author_id == user.id
        assert article.status == ArticleStatus.DRAFT

    def test_default_status_is_draft(self, db: Session):
        user = make_user(db, email="author2@test.com")
        repo = ArticleRepository(db)

        article = make_article(repo, user.id)

        assert article.status == ArticleStatus.DRAFT

    def test_cover_image_url_can_be_none(self, db: Session):
        user = make_user(db, email="author3@test.com")
        repo = ArticleRepository(db)

        article = make_article(repo, user.id, cover_image_url=None)

        assert article.cover_image_url is None


class TestGetById:
    def test_returns_article_when_exists(self, db: Session):
        user = make_user(db, email="author4@test.com")
        repo = ArticleRepository(db)
        created = make_article(repo, user.id)

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_not_exists(self, db: Session):
        repo = ArticleRepository(db)

        assert repo.get_by_id(999) is None

    def test_loads_author_relationship(self, db: Session):
        user = make_user(db, email="author5@test.com")
        repo = ArticleRepository(db)
        created = make_article(repo, user.id)

        found = repo.get_by_id(created.id)

        assert found.author.name == "Dr. Silva"


class TestGetPublished:
    def test_returns_only_published(self, db: Session):
        user = make_user(db, email="author6@test.com")
        repo = ArticleRepository(db)
        make_article(repo, user.id, status=ArticleStatus.DRAFT)
        make_article(repo, user.id, status=ArticleStatus.PUBLISHED)

        result, total = repo.get_published()

        assert len(result) == 1
        assert total == 1
        assert result[0].status == ArticleStatus.PUBLISHED

    def test_returns_empty_when_none_published(self, db: Session):
        user = make_user(db, email="author7@test.com")
        repo = ArticleRepository(db)
        make_article(repo, user.id, status=ArticleStatus.DRAFT)

        result, total = repo.get_published()

        assert result == []
        assert total == 0


class TestUpdate:
    def test_persists_changes(self, db: Session):
        user = make_user(db, email="author8@test.com")
        repo = ArticleRepository(db)
        article = make_article(repo, user.id, title="Original")

        updated = repo.update(article, {"title": "Atualizado"})

        assert updated.title == "Atualizado"

    def test_can_change_status_to_published(self, db: Session):
        user = make_user(db, email="author9@test.com")
        repo = ArticleRepository(db)
        article = make_article(repo, user.id, status=ArticleStatus.DRAFT)

        updated = repo.update(article, {"status": ArticleStatus.PUBLISHED})

        assert updated.status == ArticleStatus.PUBLISHED


class TestGetAll:
    def test_returns_all_articles_including_drafts(self, db: Session):
        user = make_user(db, email="author10@test.com")
        repo = ArticleRepository(db)
        make_article(repo, user.id, status=ArticleStatus.DRAFT)
        make_article(repo, user.id, status=ArticleStatus.PUBLISHED)

        result, total = repo.get_all()

        assert total == 2
        assert len(result) == 2

    def test_returns_empty_when_no_articles(self, db: Session):
        repo = ArticleRepository(db)

        result, total = repo.get_all()

        assert result == []
        assert total == 0

    def test_pagination_limits_results(self, db: Session):
        user = make_user(db, email="author11@test.com")
        repo = ArticleRepository(db)
        for i in range(3):
            make_article(repo, user.id, title=f"Artigo {i}")

        result, total = repo.get_all(page=1, limit=2)

        assert total == 3
        assert len(result) == 2

    def test_get_published_pagination(self, db: Session):
        user = make_user(db, email="author12@test.com")
        repo = ArticleRepository(db)
        for i in range(3):
            make_article(
                repo, user.id, status=ArticleStatus.PUBLISHED, title=f"Pub {i}"
            )

        result, total = repo.get_published(page=1, limit=2)

        assert total == 3
        assert len(result) == 2
