from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class ValidationBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid",
        validate_assignment=True
    )

class BrandModel(ValidationBaseModel):
    brand_name: str = Field(max_length=20)
    country: str = Field(max_length=20)
    active_since: date = Field(gt="1980-01-01")

class DeviceModel(ValidationBaseModel):
    brand_id: int | None = None
    device_type: str = Field(max_length=20)
    device_name: str = Field(max_length=20)
    launch_date: date
    device_price: int

class StocksModel(ValidationBaseModel):
    device_id: int | None = None
    supply_date: date
    quantity: int
    value: float