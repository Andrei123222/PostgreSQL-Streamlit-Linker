from pydantic import BaseModel, ConfigDict, Field

class ValidationBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid",
        validate_assignment=True
    )

class TypeModel(ValidationBaseModel):
    pet_type : str = Field(max_length=20)
    weight_range : str = Field(max_length=10)
    height_range : str = Field(max_length=10)

class PetModel(ValidationBaseModel):
    pet_name : str = Field(max_length=15)
    type_id : int | None = None
    age : int | None

class PersonModel(ValidationBaseModel):
    pet_id : int | None
    name : str = Field(max_length=20)
    occupation : str = Field(max_length=40)
    nickname : str | None = Field(max_length=20)