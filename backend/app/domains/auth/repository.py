from __future__ import annotations

import hashlib
import hmac

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


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
