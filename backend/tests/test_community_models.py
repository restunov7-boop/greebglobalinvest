from sqlalchemy import UniqueConstraint

from app.community import models as community_models
from app.database import Base


def test_community_foundation_tables_are_registered():
    expected_tables = {
        "community_posts",
        "community_insights",
        "community_reactions",
        "community_content_reads",
        "community_chat_links",
        "community_exchanges",
        "community_notifications",
        "community_notification_settings",
        "community_project_links",
        "community_project_pages",
        "community_admin_audit_log",
    }

    assert expected_tables.issubset(Base.metadata.tables)


def test_community_product_tables_are_registered():
    expected_tables = {
        "community_products",
        "community_product_materials",
        "community_product_access",
    }

    assert expected_tables.issubset(Base.metadata.tables)


def test_community_foundation_tables_are_project_scoped():
    for table_name in (
        "community_posts",
        "community_insights",
        "community_reactions",
        "community_content_reads",
        "community_chat_links",
        "community_exchanges",
        "community_notifications",
        "community_notification_settings",
        "community_project_links",
        "community_project_pages",
        "community_admin_audit_log",
    ):
        assert "project_id" in Base.metadata.tables[table_name].columns


def test_community_product_tables_are_project_scoped():
    for table_name in (
        "community_products",
        "community_product_materials",
        "community_product_access",
    ):
        assert "project_id" in Base.metadata.tables[table_name].columns


def test_community_user_owned_tables_have_project_user_id():
    for table_name in (
        "community_reactions",
        "community_content_reads",
        "community_notifications",
        "community_notification_settings",
    ):
        assert "project_user_id" in Base.metadata.tables[table_name].columns


def test_community_product_access_uses_project_user_id():
    assert "project_user_id" in Base.metadata.tables["community_product_access"].columns


def test_community_unique_constraints_are_declared():
    expected_constraints = {
        "community_reactions": "uq_community_reactions_project_user_target_reaction",
        "community_content_reads": "uq_community_content_reads_project_user_content",
        "community_notification_settings": "uq_community_notification_settings_project_user",
        "community_project_pages": "uq_community_project_pages_project_slug",
    }

    for table_name, constraint_name in expected_constraints.items():
        constraints = {
            constraint.name
            for constraint in Base.metadata.tables[table_name].constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert constraint_name in constraints


def test_community_product_unique_constraints_are_declared():
    expected_constraints = {
        "community_products": "uq_community_products_project_slug",
        "community_product_access": "uq_community_product_access_project_product_user",
    }

    for table_name, constraint_name in expected_constraints.items():
        constraints = {
            constraint.name
            for constraint in Base.metadata.tables[table_name].constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert constraint_name in constraints


def test_community_allowed_constants_match_foundation_scope():
    assert community_models.COMMUNITY_CONTENT_STATUSES == ("draft", "scheduled", "published", "hidden")
    assert community_models.COMMUNITY_TARGET_TYPES == ("post", "insight")
    assert community_models.COMMUNITY_REACTION_TYPES == ("useful",)
    assert community_models.COMMUNITY_NOTIFICATION_TYPES == ("urgent_insight", "system", "access")
    assert community_models.COMMUNITY_PROJECT_LINK_TYPES == (
        "support",
        "telegram_bot",
        "website",
        "blogger_telegram",
    )


def test_community_product_constants_match_product_scope():
    assert community_models.COMMUNITY_PRODUCT_ACCESS_DURATION_TYPES == ("lifetime", "fixed_until", "custom")
    assert community_models.COMMUNITY_PRODUCT_MATERIAL_TYPES == ("text", "link", "file_view", "external_site")
    assert community_models.COMMUNITY_PRODUCT_ACCESS_STATES == ("active", "expired", "revoked")
    assert community_models.COMMUNITY_PRODUCT_ACCESS_SOURCES == (
        "manual",
        "legacy_import",
        "csv_import",
        "sql_import",
        "future_payment",
    )
    assert community_models.PRODUCT_ACCESS_DURATION_LIFETIME == "lifetime"
    assert community_models.PRODUCT_MATERIAL_TYPE_TEXT == "text"
    assert community_models.PRODUCT_ACCESS_STATE_ACTIVE == "active"
    assert community_models.PRODUCT_ACCESS_SOURCE_MANUAL == "manual"
