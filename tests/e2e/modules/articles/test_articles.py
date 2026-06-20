import bcrypt
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.modules.articles.model import Article, ArticleStatus
from app.modules.articles.repository import ArticleRepository

BASE_URL = "/api/v1/articles"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def make_article(db: Session, author_id: int, **kwargs):
    repo = ArticleRepository(db)
    defaults = {
        "title": "Artigo E2E",
        "content": "Conteúdo do artigo",
        "category": "Direito Civil",
        "summary": "Resumo do artigo",
        "author_id": author_id,
        "cover_image_url": None,
        "status": ArticleStatus.DRAFT,
    }
    defaults.update(kwargs)
    article = repo.create(**defaults)
    db.commit()
    return article


class TestCreateArticle:
    def test_returns_201_with_token(self, client, user_headers, db_session):
        response = client.post(
            BASE_URL,
            json={
                "title": "Novo",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo do artigo",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.status_code == 201

    def test_returns_401_without_token(self, client):
        response = client.post(
            BASE_URL,
            json={
                "title": "Novo",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo do artigo",
            },
        )

        assert response.status_code == 401

    def test_default_status_is_draft(self, client, user_headers, db_session):
        response = client.post(
            BASE_URL,
            json={
                "title": "Rascunho",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo do artigo",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.json()["data"]["status"] == "draft"

    def test_can_create_as_published(self, client, user_headers, db_session):
        response = client.post(
            BASE_URL,
            json={
                "title": "Pub",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo do artigo",
                "status": "published",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.json()["data"]["status"] == "published"

    def test_returns_author_name(self, client, user_headers, active_user, db_session):
        response = client.post(
            BASE_URL,
            json={
                "title": "Autor",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo do artigo",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.json()["data"]["author_name"] is not None


class TestUpdateArticle:
    def test_returns_200_with_token(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(db_session, active_user["id"])

        response = client.patch(
            f"{BASE_URL}/{article.id}",
            json={"title": "Atualizado"},
            headers=user_headers,
        )
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 200

    def test_returns_401_without_token(self, client, active_user, db_session):
        article = make_article(db_session, active_user["id"])

        response = client.patch(f"{BASE_URL}/{article.id}", json={"title": "X"})
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 401

    def test_returns_404_for_missing_article(self, client, user_headers):
        response = client.patch(
            f"{BASE_URL}/999999",
            json={"title": "X"},
            headers=user_headers,
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ARTICLE_NOT_FOUND"

    def test_can_publish_draft(self, client, user_headers, active_user, db_session):
        article = make_article(
            db_session, active_user["id"], status=ArticleStatus.DRAFT
        )

        response = client.patch(
            f"{BASE_URL}/{article.id}",
            json={"status": "published"},
            headers=user_headers,
        )
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.json()["data"]["status"] == "published"


class TestPreviewArticle:
    def test_returns_200_with_token_for_draft(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(
            db_session, active_user["id"], status=ArticleStatus.DRAFT
        )

        response = client.get(f"{BASE_URL}/{article.id}/preview", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 200

    def test_returns_401_without_token(self, client, active_user, db_session):
        article = make_article(db_session, active_user["id"])

        response = client.get(f"{BASE_URL}/{article.id}/preview")
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 401

    def test_returns_404_for_missing_article(self, client, user_headers):
        response = client.get(f"{BASE_URL}/999999/preview", headers=user_headers)

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ARTICLE_NOT_FOUND"

    def test_draft_visible_in_preview(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(
            db_session, active_user["id"], status=ArticleStatus.DRAFT
        )

        response = client.get(f"{BASE_URL}/{article.id}/preview", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.json()["data"]["status"] == "draft"


class TestListArticles:
    def test_returns_200_without_token(self, client):
        response = client.get(BASE_URL)

        assert response.status_code == 200

    def test_draft_not_in_public_list(self, client, active_user, db_session):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.DRAFT,
            title="Rascunho Secreto",
        )

        response = client.get(BASE_URL)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        titles = [a["title"] for a in response.json()["data"]]
        assert "Rascunho Secreto" not in titles

    def test_published_appears_in_public_list(self, client, active_user, db_session):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.PUBLISHED,
            title="Artigo Público",
        )

        response = client.get(BASE_URL)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        titles = [a["title"] for a in response.json()["data"]]
        assert "Artigo Público" in titles

    def test_list_item_has_status_field(self, client, active_user, db_session):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.PUBLISHED,
            title="Com Status",
        )

        response = client.get(BASE_URL)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        matching = [a for a in response.json()["data"] if a["title"] == "Com Status"]
        assert len(matching) == 1
        assert matching[0]["status"] == "published"

    def test_list_item_has_author_name_and_category(
        self, client, active_user, db_session
    ):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.PUBLISHED,
            title="Com Author",
            category="Direito Civil",
        )

        response = client.get(BASE_URL)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        matching = [a for a in response.json()["data"] if a["title"] == "Com Author"]
        assert len(matching) == 1
        assert matching[0]["author_name"] is not None
        assert matching[0]["category"] == "Direito Civil"


class TestListAllArticles:
    def test_returns_200_with_token(self, client, user_headers):
        response = client.get(f"{BASE_URL}/admin", headers=user_headers)

        assert response.status_code == 200

    def test_returns_401_without_token(self, client):
        response = client.get(f"{BASE_URL}/admin")

        assert response.status_code == 401

    def test_includes_drafts(self, client, user_headers, active_user, db_session):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.DRAFT,
            title="Rascunho Admin",
        )

        response = client.get(f"{BASE_URL}/admin", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        titles = [a["title"] for a in response.json()["data"]]
        assert "Rascunho Admin" in titles

    def test_list_item_has_status_field(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(
            db_session, active_user["id"], status=ArticleStatus.DRAFT
        )

        response = client.get(f"{BASE_URL}/admin", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert all("status" in item for item in response.json()["data"])

    def test_list_item_has_author_name_and_category(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(
            db_session,
            active_user["id"],
            status=ArticleStatus.DRAFT,
            title="Admin Author",
            category="Trabalhista",
        )

        response = client.get(f"{BASE_URL}/admin", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        matching = [a for a in response.json()["data"] if a["title"] == "Admin Author"]
        assert len(matching) == 1
        assert matching[0]["author_name"] is not None
        assert matching[0]["category"] == "Trabalhista"


class TestCoverImagePosition:
    def test_cover_image_position_defaults_to_null(
        self, client, user_headers, db_session
    ):
        response = client.post(
            BASE_URL,
            json={
                "title": "Sem posição",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.json()["data"]["cover_image_position"] is None

    def test_create_with_cover_image_position(self, client, user_headers, db_session):
        response = client.post(
            BASE_URL,
            json={
                "title": "Com posição",
                "content": "Texto",
                "category": "Civil",
                "summary": "Resumo",
                "cover_image_url": "https://example.com/img.jpg",
                "cover_image_position": "30,70",
            },
            headers=user_headers,
        )
        article_id = response.json()["data"]["id"]
        db_session.execute(delete(Article).where(Article.id == article_id))
        db_session.commit()

        assert response.status_code == 201
        assert response.json()["data"]["cover_image_position"] == "30,70"

    def test_update_cover_image_position(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(db_session, active_user["id"])

        response = client.patch(
            f"{BASE_URL}/{article.id}",
            json={"cover_image_position": "80,20"},
            headers=user_headers,
        )
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 200
        assert response.json()["data"]["cover_image_position"] == "80,20"

    def test_cover_image_position_present_in_preview_response(
        self, client, user_headers, active_user, db_session
    ):
        article = make_article(
            db_session, active_user["id"], cover_image_position="50,50"
        )

        response = client.get(f"{BASE_URL}/{article.id}/preview", headers=user_headers)
        db_session.execute(delete(Article).where(Article.id == article.id))
        db_session.commit()

        assert response.status_code == 200
        assert response.json()["data"]["cover_image_position"] == "50,50"


class TestCreateArticleValidation:
    def test_returns_422_for_empty_title(self, client, user_headers):
        response = client.post(
            BASE_URL,
            json={"title": "", "content": "Texto", "category": "Civil"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_for_empty_content(self, client, user_headers):
        response = client.post(
            BASE_URL,
            json={"title": "Título", "content": "", "category": "Civil"},
            headers=user_headers,
        )

        assert response.status_code == 422

    def test_returns_422_for_empty_category(self, client, user_headers):
        response = client.post(
            BASE_URL,
            json={"title": "Título", "content": "Texto", "category": ""},
            headers=user_headers,
        )

        assert response.status_code == 422
