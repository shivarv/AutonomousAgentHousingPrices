from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ping(self) -> bool:
        return self.session.execute(text("SELECT 1")).scalar_one() == 1
