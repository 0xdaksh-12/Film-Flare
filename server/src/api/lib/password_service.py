import bcrypt


class PasswordService:
    """Handle password hashing and verification"""

    @staticmethod
    def hashed(password: str) -> str:

        return bcrypt.hashpw(
            password=password[:72].encode("utf-8"), salt=bcrypt.gensalt()
        ).decode("utf-8")

    @staticmethod
    def compareHash(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password=password[:72].encode("utf-8"),
            hashed_password=hashed.encode("utf-8"),
        )
