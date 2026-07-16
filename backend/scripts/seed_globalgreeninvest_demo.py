from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.community.models import (  # noqa: E402
    CommunityChatLink,
    CommunityExchange,
    CommunityInsight,
    CommunityPost,
    CommunityProduct,
    CommunityProductAccess,
    CommunityProductMaterial,
    CommunityProjectLink,
    CommunityProjectPage,
)
from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.projects.models import Project, ProjectUser  # noqa: E402
from app.users.models import TelegramIdentity, User  # noqa: E402

PROJECT_SLUG = "global-green-invest"
PROJECT_NAME = "GlobalGreenInvest / 🍀 ЗЕЛЁНЫЙ / TG Investor"
DISCLAIMER = (
    "Материалы внутри приложения отражают мнение команды и не являются финансовой рекомендацией. "
    "Пользователь самостоятельно принимает решения и несёт ответственность за свои действия."
)


def main() -> None:
    db = SessionLocal()
    try:
        project = _ensure_project(db)
        admin = _ensure_demo_admin(db, project)
        dev_project_user = _ensure_dev_project_user(db, project)
        content_owner = dev_project_user or admin
        _seed_links(db, project)
        _seed_pages(db, project)
        _seed_chats(db, project, content_owner)
        _seed_exchanges(db, project, content_owner)
        _seed_posts_and_insights(db, project, content_owner)
        products = _seed_products(db, project, content_owner)
        _grant_demo_access(db, project, admin, products[:2])
        if dev_project_user is not None:
            _grant_demo_access(db, project, dev_project_user, products[:2])
        db.commit()
        print(f"GlobalGreenInvest demo seed complete: project={project.slug}, products={len(products)}")
    finally:
        db.close()


def _ensure_project(db) -> Project:
    project = db.query(Project).filter(Project.slug == PROJECT_SLUG).one_or_none()
    if project is None:
        project = Project(slug=PROJECT_SLUG, name=PROJECT_NAME, is_active=True)
        db.add(project)
        db.flush()
    else:
        project.name = PROJECT_NAME
        project.is_active = True
    return project


def _ensure_demo_admin(db, project: Project) -> ProjectUser:
    user = db.query(User).filter(User.display_name == "GlobalGreenInvest Demo Admin").one_or_none()
    if user is None:
        user = User(display_name="GlobalGreenInvest Demo Admin", is_active=True)
        db.add(user)
        db.flush()
    project_user = db.query(ProjectUser).filter(ProjectUser.user_id == user.id, ProjectUser.project_id == project.id).one_or_none()
    if project_user is None:
        project_user = ProjectUser(
            user_id=user.id,
            project_id=project.id,
            role="owner",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(project_user)
        db.flush()
    else:
        project_user.role = "owner"
        project_user.status = "active"
        project_user.access_state = "active"
        project_user.moderation_state = "normal"
    return project_user


def _ensure_dev_project_user(db, project: Project) -> ProjectUser | None:
    if settings.app_env == "production" or not settings.dev_auth_enabled:
        return None
    identity = db.query(TelegramIdentity).filter(TelegramIdentity.telegram_id == settings.dev_telegram_id).one_or_none()
    if identity is None:
        user = User(display_name=settings.dev_telegram_first_name or "CORE Dev User", is_active=True)
        db.add(user)
        db.flush()
        identity = TelegramIdentity(
            user_id=user.id,
            telegram_id=settings.dev_telegram_id,
            username=settings.dev_telegram_username,
            first_name=settings.dev_telegram_first_name,
            raw_data_json={"source": "globalgreeninvest_demo_seed"},
        )
        db.add(identity)
        db.flush()
    else:
        user = identity.user
        user.is_active = True
    project_user = db.query(ProjectUser).filter(ProjectUser.user_id == user.id, ProjectUser.project_id == project.id).one_or_none()
    if project_user is None:
        project_user = ProjectUser(
            user_id=user.id,
            project_id=project.id,
            role="owner",
            status="active",
            is_premium=False,
            access_state="active",
            access_until=datetime.now(UTC) + timedelta(days=365),
            moderation_state="normal",
        )
        db.add(project_user)
        db.flush()
    else:
        project_user.role = "owner"
        project_user.status = "active"
        project_user.access_state = "active"
        project_user.access_until = datetime.now(UTC) + timedelta(days=365)
        project_user.moderation_state = "normal"
    return project_user


def _seed_links(db, project: Project) -> None:
    links = {
        "support": ("Поддержка", os.getenv("GGI_SUPPORT_URL", "https://t.me/demo_globalgreen_support")),
        "telegram_bot": ("Telegram-бот", os.getenv("GGI_BOT_URL", "https://t.me/demo_globalgreen_bot")),
        "website": ("Сайт", os.getenv("GGI_WEBSITE_URL", "https://example.com/globalgreeninvest-demo")),
        "blogger_telegram": ("Telegram блогера", os.getenv("GGI_BLOGGER_URL", "https://t.me/demo_globalgreen_blogger")),
    }
    for link_type, (title, url) in links.items():
        row = db.query(CommunityProjectLink).filter(CommunityProjectLink.project_id == project.id, CommunityProjectLink.type == link_type).one_or_none()
        if row is None:
            row = CommunityProjectLink(project_id=project.id, type=link_type, title=title, url=url, is_active=True)
            db.add(row)
        else:
            row.title = title
            row.url = url
            row.is_active = True


def _seed_pages(db, project: Project) -> None:
    pages = {
        "about": ("О проекте", "Закрытое приложение GlobalGreenInvest для материалов, ссылок и продуктовых доступов TG Investor."),
        "rules": ("Правила", "Материалы предназначены для участников закрытого сообщества. Не распространяйте закрытый контент публично."),
        "disclaimer": ("Дисклеймер", DISCLAIMER),
    }
    for slug, (title, content) in pages.items():
        page = db.query(CommunityProjectPage).filter(CommunityProjectPage.project_id == project.id, CommunityProjectPage.slug == slug).one_or_none()
        if page is None:
            page = CommunityProjectPage(project_id=project.id, slug=slug, title=title, content=content, is_published=True)
            db.add(page)
        else:
            page.title = title
            page.content = content
            page.is_published = True


def _seed_chats(db, project: Project, admin: ProjectUser) -> None:
    for index, title in enumerate(["Основной чат", "Инсайды", "Поддержка"], start=1):
        chat = db.query(CommunityChatLink).filter(CommunityChatLink.project_id == project.id, CommunityChatLink.title == title).one_or_none()
        if chat is None:
            db.add(
                CommunityChatLink(
                    project_id=project.id,
                    created_by_project_user_id=admin.id,
                    title=title,
                    telegram_url=f"https://t.me/demo_globalgreen_chat_{index}",
                    sort_order=index,
                    is_published=True,
                )
            )
        else:
            chat.telegram_url = f"https://t.me/demo_globalgreen_chat_{index}"
            chat.sort_order = index
            chat.is_published = True


def _seed_exchanges(db, project: Project, admin: ProjectUser) -> None:
    for index, title in enumerate(["Demo Exchange One", "Demo Exchange Two", "Demo Exchange Three"], start=1):
        exchange = db.query(CommunityExchange).filter(CommunityExchange.project_id == project.id, CommunityExchange.title == title).one_or_none()
        data = {
            "description": "Демо-площадка для проверки интерфейса. Не является рекомендацией.",
            "team_comment": "Проверьте условия самостоятельно перед любым действием.",
            "external_url": f"https://example.com/exchange-{index}",
            "promo_code": f"DEMO{index}",
            "sort_order": index,
            "is_published": True,
        }
        if exchange is None:
            db.add(CommunityExchange(project_id=project.id, created_by_project_user_id=admin.id, title=title, **data))
        else:
            for key, value in data.items():
                setattr(exchange, key, value)


def _seed_posts_and_insights(db, project: Project, admin: ProjectUser) -> None:
    now = datetime.now(UTC)
    posts = [("Старт проекта", True), ("Операционный обзор", False), ("Как пользоваться приложением", False), ("Материалы и доступы", False)]
    for index, (title, pinned) in enumerate(posts):
        post = db.query(CommunityPost).filter(CommunityPost.project_id == project.id, CommunityPost.title == title).one_or_none()
        data = {
            "excerpt": "Демо-материал для презентации закрытого приложения.",
            "content": f"{title}\n\nНейтральный демонстрационный текст без финансовых обещаний.",
            "status": "published",
            "is_pinned": pinned,
            "published_at": now - timedelta(hours=index + 1),
        }
        if post is None:
            db.add(CommunityPost(project_id=project.id, author_project_user_id=admin.id, title=title, **data))
        else:
            for key, value in data.items():
                setattr(post, key, value)
    insights = [("Срочный демо-инсайд", True), ("Еженедельный обзор", False), ("Риск-контроль", False)]
    for index, (title, urgent) in enumerate(insights):
        insight = db.query(CommunityInsight).filter(CommunityInsight.project_id == project.id, CommunityInsight.title == title).one_or_none()
        data = {
            "excerpt": "Демо-инсайд для проверки интерфейса.",
            "content": f"{title}\n\nИнформационный материал без инвестиционной рекомендации.",
            "is_urgent": urgent,
            "status": "published",
            "published_at": now - timedelta(minutes=30 + index),
        }
        if insight is None:
            db.add(CommunityInsight(project_id=project.id, author_project_user_id=admin.id, title=title, **data))
        else:
            for key, value in data.items():
                setattr(insight, key, value)


def _seed_products(db, project: Project, admin: ProjectUser) -> list[CommunityProduct]:
    titles = [
        ("skins-farm-type-1", "Ферма скинов — Тип 1"),
        ("skins-farm-type-2", "Ферма скинов — Тип 2"),
        ("trading-courses", "Курсы по трейдингу"),
        ("trading-bot", "Трейдинг-бот"),
        ("invest-portfolio", "Инвест-портфель"),
    ]
    products = []
    for index, (slug, title) in enumerate(titles, start=1):
        product = db.query(CommunityProduct).filter(CommunityProduct.project_id == project.id, CommunityProduct.slug == slug).one_or_none()
        data = {
            "title": title,
            "short_description": "Демо-продукт для презентации структуры материалов.",
            "description": f"{title}. Описание демонстрирует карточку продукта и закрытые материалы без финансовых обещаний.",
            "price_usd": None,
            "price_rub": None,
            "sort_order": index,
            "is_published": True,
            "access_duration_type": "lifetime",
        }
        if product is None:
            product = CommunityProduct(project_id=project.id, created_by_project_user_id=admin.id, slug=slug, **data)
            db.add(product)
            db.flush()
        else:
            for key, value in data.items():
                setattr(product, key, value)
        _seed_materials(db, project, product)
        products.append(product)
    return products


def _seed_materials(db, project: Project, product: CommunityProduct) -> None:
    materials = [
        ("Вводный материал", "text", "Открытый вводный текст продукта.", None, None, 1, False),
        ("Закрытый текст", "text", "Закрытый демо-материал продукта.", None, None, 2, True),
        ("Закрытая ссылка", "link", None, "https://example.com/locked-material", None, 3, True),
    ]
    for title, material_type, content, url, file_url, sort_order, is_locked in materials:
        material = (
            db.query(CommunityProductMaterial)
            .filter(CommunityProductMaterial.project_id == project.id, CommunityProductMaterial.product_id == product.id, CommunityProductMaterial.title == title)
            .one_or_none()
        )
        data = {
            "material_type": material_type,
            "description": "Демо-материал",
            "content": content,
            "url": url,
            "file_url": file_url,
            "sort_order": sort_order,
            "is_locked": is_locked,
            "deleted_at": None,
        }
        if material is None:
            db.add(CommunityProductMaterial(project_id=project.id, product_id=product.id, title=title, **data))
        else:
            for key, value in data.items():
                setattr(material, key, value)


def _grant_demo_access(db, project: Project, admin: ProjectUser, products: list[CommunityProduct]) -> None:
    for product in products:
        access = (
            db.query(CommunityProductAccess)
            .filter(
                CommunityProductAccess.project_id == project.id,
                CommunityProductAccess.product_id == product.id,
                CommunityProductAccess.project_user_id == admin.id,
            )
            .one_or_none()
        )
        if access is None:
            access = CommunityProductAccess(project_id=project.id, product_id=product.id, project_user_id=admin.id)
            db.add(access)
        access.access_state = "active"
        access.access_until = None
        access.source = "manual"
        access.granted_by_project_user_id = admin.id


if __name__ == "__main__":
    main()
