import pyotp


def generate_secret() -> str:
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, badge_id: str, issuer: str = "ForenChain") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=badge_id, issuer_name=issuer)


def verify(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    # valid_window=1 allows ±30 seconds of clock drift
    return totp.verify(code, valid_window=1)
