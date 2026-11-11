from app.dao.shelter_dao import ShelterDao
from app.schemas.shelter import ShelterList, ShelterRead

NOTE = (
    "Shelter locations are public OpenStreetMap features; domestic-violence shelters are "
    "excluded. Bed counts are published only per Continuum of Care (HUD HIC), see "
    "/api/homelessness."
)


class ShelterService:
    def __init__(self, dao: ShelterDao) -> None:
        self.dao = dao

    def list(self, coc_number: str | None = None) -> ShelterList:
        rows = self.dao.list_all(coc_number)
        return ShelterList(
            shelters=[
                ShelterRead(
                    **{k: v for k, v in r._mapping.items() if k != "source_key"},
                    source=r.source_key,
                )
                for r in rows
            ],
            note=NOTE,
        )
