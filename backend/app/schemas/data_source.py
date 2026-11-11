from datetime import date

from pydantic import BaseModel, ConfigDict


class DataSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    url: str
    download_date: date
    licence: str
    geography: str
    years: str
    file_path: str
    columns_used: str
