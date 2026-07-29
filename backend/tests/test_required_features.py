from io import BytesIO

from openpyxl import Workbook

from app.core.config import PoServer
from app.domains.auth import repository as auth_module
from app.domains.auth.repository import UserRepository
from app.domains.channels.bulk_service import ChannelBulkService
from app.domains.hrd.service import generate_excel, parse_query_statement
from app.domains.messages.service import MessageService
from app.domains.oracle_ifs.service import OracleIfsService
from app.domains.posts import repository as posts_module
from app.domains.posts.repository import PostRepository


def test_hrd_parser_and_excel_contract() -> None:
    table, companies = parse_query_statement(
        "select * FROM OWNER.MDM_IF_FA where COMPANY_CD IN ('1000', '2000')"
    )
    assert table == "MDM_IF_FA"
    assert companies == ["1000", "2000"]
    content = generate_excel(
        [{
            "if_id": "HRD001",
            "dist_if_id": "DIST_HRD001",
            "table_name": table,
            "batch_tm": "0 0 * * *",
            "company_cd": companies,
            "dist_cnt": 2,
            "match_type": "ALL",
            "sid": "POQ",
        }]
    )
    assert content.startswith(b"PK")


def test_channel_bulk_preview_masks_password(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.channels.service.settings.sap_po_live_mode",
        False,
    )
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["component_id", "channel_id", "dbuser", "dbpassword"])
    sheet.append(["BS_POQ", "CHANNEL_A", "user", "secret"])
    output = BytesIO()
    workbook.save(output)
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="https://example.invalid",
        capabilities=["monitor"],
    )
    result = ChannelBulkService().preview(server, output.getvalue())
    assert result["to_change"] == 1
    assert result["details"][0]["after"]["dbpassword"] == "********"


def test_admin_approved_password_reset_flow(monkeypatch) -> None:
    monkeypatch.setattr(auth_module.settings, "demo_mode", True)
    username = "reset_flow_user"
    auth_module._demo_users[username] = {
        "username": username,
        "display_name": "Reset Flow",
        "role": "VIEWER",
        "active": True,
        "first_login": True,
        "server_sids": [],
    }
    auth_module._demo_passwords[username] = "old-password"
    repository = UserRepository()
    try:
        repository.request_password_reset(username)
        request = repository.list_password_reset_requests()[-1]
        token = repository.issue_password_reset_token(request["request_id"])
        repository.consume_password_reset(token, "new-password")
        assert repository.authenticate(username, "new-password") is not None
    finally:
        auth_module._demo_users.pop(username, None)
        auth_module._demo_passwords.pop(username, None)
        auth_module._demo_reset_requests[:] = [
            row for row in auth_module._demo_reset_requests
            if row["username"] != username
        ]


def test_posts_crud_and_ownership(monkeypatch) -> None:
    monkeypatch.setattr(posts_module.settings, "demo_mode", True)
    posts_module._demo_posts.clear()
    repository = PostRepository()
    row = repository.create("operator", "Title", "Content", "OPERATIONS")
    updated = repository.update(
        row["post_id"], "operator", False, "Changed", "Content", "OPERATIONS"
    )
    assert updated["title"] == "Changed"
    repository.delete(row["post_id"], "admin", True)
    assert repository.list() == []


def test_oracle_ifs_grouping_deduplicates_ifs_ids() -> None:
    rows = [
        ("user1", "REQ-1", "IFS-A", "ERP", "REST", "MES", "SOAP", "READY", None),
        ("user1", "REQ-1", "IFS-A", "ERP", "REST", "MES", "SOAP", "READY", None),
        ("user1", "REQ-1", "IFS-B", "ERP", "REST", "MES", "SOAP", "READY", None),
    ]
    grouped = OracleIfsService._group(rows)
    assert grouped[0]["ifs_ids"] == ["IFS-A", "IFS-B"]


def test_message_daily_check_filters_delivering_and_keyword(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.messages.service.settings.sap_po_live_mode",
        False,
    )
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="https://example.invalid",
        capabilities=["monitor"],
    )
    delivering = MessageService().list_recent(
        server,
        100,
        hours=168,
        status="DELIVERING",
    )
    hrd = MessageService().list_recent(
        server,
        100,
        hours=168,
        keyword="HRD",
    )
    assert delivering and all(row["status"] == "DELIVERING" for row in delivering)
    assert hrd and all("HRD" in row["interface_name"] for row in hrd)


def test_required_feature_routes_are_registered() -> None:
    from app.main import app

    paths = app.openapi()["paths"]
    required = {
        "/api/v1/hrd/interfaces",
        "/api/v1/hrd/interfaces/excel",
        "/api/v1/hrd/test-message",
        "/api/v1/channels/batch-control-stream",
        "/api/v1/channels/bulk-export",
        "/api/v1/channels/bulk-preview",
        "/api/v1/interfaces/namespaces",
        "/api/v1/monitoring/system-statistics",
        "/api/v1/monitoring/system-queue-status",
        "/api/v1/monitoring/throughput",
        "/api/v1/oracle-ifs/interfaces",
        "/api/v1/oracle-ifs/sync",
        "/api/v1/posts",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/change-password",
    }
    assert required.issubset(paths)
