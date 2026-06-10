from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _ctx.hash(plain)


def verify(plain: str, hashed: str) -> bool:
    return _ctx.verify(plain, hashed)
