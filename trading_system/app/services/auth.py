from fastapi import Header, HTTPException, status


def require_bearer_token(authorization: str | None, expected_token: str) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")


async def bot_auth_dependency(authorization: str | None = Header(default=None)) -> str:
    return authorization or ""
