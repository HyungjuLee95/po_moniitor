from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import require_permissions
from app.domains.posts.repository import PostRepository


router = APIRouter(prefix="/posts", tags=["Posts"])


class PostWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)
    category: str = Field(default="GENERAL", min_length=1, max_length=64)


@router.get("")
def list_posts(_: dict = Depends(require_permissions("posts:read"))) -> dict:
    rows = PostRepository().list()
    return {"data": rows, "meta": {"count": len(rows)}}


@router.post("", status_code=201)
def create_post(
    payload: PostWrite,
    user: dict = Depends(require_permissions("posts:write")),
) -> dict:
    return {
        "data": PostRepository().create(
            user["username"], payload.title, payload.content, payload.category
        )
    }


@router.put("/{post_id}")
def update_post(
    post_id: int,
    payload: PostWrite,
    user: dict = Depends(require_permissions("posts:write")),
) -> dict:
    try:
        row = PostRepository().update(
            post_id,
            user["username"],
            user["role"] == "ADMIN",
            payload.title,
            payload.content,
            payload.category,
        )
        return {"data": row}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="post not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="post ownership required") from exc


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    user: dict = Depends(require_permissions("posts:write")),
) -> None:
    try:
        PostRepository().delete(post_id, user["username"], user["role"] == "ADMIN")
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="post not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="post ownership required") from exc
