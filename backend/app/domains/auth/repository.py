from __future__ import annotations

import hashlib
import hmac
import os

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


ROLE_CODES = {"ADMIN", "OPERATOR", "VIEWER"}
_demo_users: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "display_name": "System Admin",
        "role": "ADMIN",
        "active": True,
        "first_login": False,
        "server_sids": [],
    },
    "operator": {
        "username": "operator",
        "display_name": "Operations Manager",
        "role": "OPERATOR",
        "active": True,
        "first_login": True,
        "server_sids": [],
    },
    "viewer": {
        "username": "viewer",
        "display_name": "General User",
        "role": "VIEWER",
        "active": True,
        "first_login": True,
        "server_sids": [],
    },
}


def hash_password(password: str, iterations: int = 310_000) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


class UserRepository:
    def authenticate(self, username: str, password: str) -> dict | None:
        if settings.demo_mode:
            if (
                username == settings.demo_admin_username
                and password == settings.demo_admin_password
            ):
                return {"username": username, "display_name": "Demo Administrator", "role": "ADMIN"}
            return None

        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    select u.username, u.display_name, u.password_hash, r.role_code
                    from iam.app_user u
                    join iam.user_role ur on ur.user_id = u.user_id
                    join iam.app_role r on r.role_code = ur.role_code
                    where u.username = :username and u.active = true
                    order by case r.role_code when 'ADMIN' then 1 when 'OPERATOR' then 2 else 3 end
                    limit 1
                    """
                ),
                {"username": username},
            ).mappings().first()
        if not row or not verify_password(password, row["password_hash"]):
            return None
        return {
            "username": row["username"],
            "display_name": row["display_name"],
            "role": row["role_code"],
        }

    def list_users(self) -> list[dict]:
        if settings.demo_mode:
            return [dict(row) for row in _demo_users.values()]

        with session_scope() as session:
            rows = session.execute(
                text(
                    """
                    select u.username, u.display_name, u.active, u.first_login,
                           r.role_code as role,
                           coalesce(
                               array_agg(us.sid order by us.sid)
                                   filter (where us.sid is not null),
                               array[]::varchar[]
                           ) as server_sids
                    from iam.app_user u
                    join iam.user_role ur on ur.user_id = u.user_id
                    join iam.app_role r on r.role_code = ur.role_code
                    left join iam.user_server us on us.user_id = u.user_id
                    group by u.user_id, r.role_code
                    order by u.active desc, u.username
                    """
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    def create_user(
        self,
        username: str,
        display_name: str,
        password: str,
        role: str,
        server_sids: list[str],
        actor: str,
    ) -> dict:
        if settings.demo_mode:
            if username in _demo_users:
                raise ValueError("username already exists")
            row = {
                "username": username,
                "display_name": display_name,
                "role": role,
                "active": True,
                "first_login": True,
                "server_sids": server_sids,
            }
            _demo_users[username] = row
            return dict(row)

        with session_scope() as session:
            user_id = session.execute(
                text(
                    """
                    insert into iam.app_user (
                        username, display_name, password_hash, active, first_login
                    ) values (
                        :username, :display_name, :password_hash, true, true
                    )
                    returning user_id
                    """
                ),
                {
                    "username": username,
                    "display_name": display_name,
                    "password_hash": hash_password(password),
                },
            ).scalar_one()
            session.execute(
                text("insert into iam.user_role (user_id, role_code) values (:user_id, :role)"),
                {"user_id": user_id, "role": role},
            )
            for sid in server_sids:
                session.execute(
                    text("insert into iam.user_server (user_id, sid) values (:user_id, :sid)"),
                    {"user_id": user_id, "sid": sid},
                )
            self._audit(session, actor, username, "CREATE", {"role": role, "server_sids": server_sids})
        return self.get_user(username)

    def update_user(
        self,
        username: str,
        display_name: str,
        role: str,
        active: bool,
        server_sids: list[str],
        actor: str,
    ) -> dict:
        if settings.demo_mode:
            if username not in _demo_users:
                raise LookupError("user not found")
            _demo_users[username].update(
                display_name=display_name,
                role=role,
                active=active,
                server_sids=server_sids,
            )
            return dict(_demo_users[username])

        with session_scope() as session:
            user_id = session.execute(
                text(
                    """
                    update iam.app_user
                    set display_name = :display_name, active = :active, updated_at = now()
                    where username = :username
                    returning user_id
                    """
                ),
                {"username": username, "display_name": display_name, "active": active},
            ).scalar_one_or_none()
            if user_id is None:
                raise LookupError("user not found")
            session.execute(text("delete from iam.user_role where user_id = :user_id"), {"user_id": user_id})
            session.execute(
                text("insert into iam.user_role (user_id, role_code) values (:user_id, :role)"),
                {"user_id": user_id, "role": role},
            )
            session.execute(text("delete from iam.user_server where user_id = :user_id"), {"user_id": user_id})
            for sid in server_sids:
                session.execute(
                    text("insert into iam.user_server (user_id, sid) values (:user_id, :sid)"),
                    {"user_id": user_id, "sid": sid},
                )
            self._audit(
                session,
                actor,
                username,
                "UPDATE",
                {"role": role, "active": active, "server_sids": server_sids},
            )
        return self.get_user(username)

    def reset_password(self, username: str, password: str, actor: str) -> None:
        if settings.demo_mode:
            if username not in _demo_users:
                raise LookupError("user not found")
            _demo_users[username]["first_login"] = True
            return

        with session_scope() as session:
            updated = session.execute(
                text(
                    """
                    update iam.app_user
                    set password_hash = :password_hash, first_login = true, updated_at = now()
                    where username = :username
                    """
                ),
                {"username": username, "password_hash": hash_password(password)},
            ).rowcount
            if not updated:
                raise LookupError("user not found")
            self._audit(session, actor, username, "RESET_PASSWORD", {})

    def get_user(self, username: str) -> dict:
        for row in self.list_users():
            if row["username"] == username:
                return row
        raise LookupError("user not found")

    def allowed_sids(self, username: str, role: str) -> list[str] | None:
        if role.upper() == "ADMIN" or settings.demo_mode:
            return None
        with session_scope() as session:
            rows = session.execute(
                text(
                    """
                    select us.sid
                    from iam.user_server us
                    join iam.app_user u on u.user_id = us.user_id
                    where u.username = :username and u.active = true
                    order by us.sid
                    """
                ),
                {"username": username},
            ).scalars().all()
        return list(rows)

    @staticmethod
    def _audit(session, actor: str, target: str, action: str, detail: dict) -> None:
        session.execute(
            text(
                """
                insert into iam.access_audit (
                    actor_username, target_username, action, detail
                ) values (:actor, :target, :action, cast(:detail as jsonb))
                """
            ),
            {
                "actor": actor,
                "target": target,
                "action": action,
                "detail": __import__("json").dumps(detail),
            },
        )
