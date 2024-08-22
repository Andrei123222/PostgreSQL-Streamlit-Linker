from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

conn = st.connection("postgresql", type="sql")
DATABASE_URL = "postgresql://postgres:1q2w3e@localhost/streamLitTest"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def data_exists(table: str,column: str,data: str):
    with next(get_db_session()) as s:
        result = s.execute(text(f"SELECT COUNT(1) FROM {table} WHERE {column} = '{data}'")).fetchone()
        return result[0] > 0
    
def query_column(table: str, column: str, data: str, info: str):
    return conn.query(f"SELECT {column} FROM {table} WHERE {info} = {data}",ttl="0m").to_dict()

class ValidationBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
        extra="allow"
    )

class PetConfValidator(ValidationBaseModel):
    is_stray: bool
    address_lookup: str | None = Field(default=None,validation_alias="ref_table_name1",serialization_alias="ref_table_name1")
    lookup_column: str | None = Field(default=None,validation_alias="ref_table_column1",serialization_alias="ref_table_column1")
    owner_address: str | None = Field(max_length=30)
    type_lookup: str = Field(validation_alias="ref_table_name2",serialization_alias="ref_table_name2")
    type_column: str = Field(validation_alias="ref_table_column2",serialization_alias="ref_table_column2")
    type_id: int
    age_lookup: str | None = Field(default="types")
    age_column: str | None = Field(default="age_range")
    age : int
    pet_name: str

    @field_validator("owner_address")
    @classmethod
    def validate_address(cls, value, validated_values: ValidationInfo):
        data = validated_values.data
        if not data["is_stray"]:
            if data_exists(data["address_lookup"],data["lookup_column"],value):
                return value
            table_name = data["address_lookup"]
            raise ValueError(f"value doesn't exist in the lookup table {table_name}")
    
    @field_validator("type_id")
    @classmethod
    def validate_type(cls, value, validated_values: ValidationInfo):
        data = validated_values.data
        if data_exists(data["type_lookup"],data["type_column"],value):
            return value
        table_name = data["type_lookup"]
        raise ValueError(f"Value doesn't exist in the lookup table {table_name}")
    
    @field_validator("age")
    @classmethod
    def validate_age(cls, value, validated_values: ValidationInfo):
        data = validated_values.data
        info = query_column(data["age_lookup"],data["age_column"],data["type_id"],"type_id")
        
        if info["age_range"][0] != None:
            values = info["age_range"][0].split('-')
            if value > int(values[0]) and value < int(values[1]):
                return value
            else:
                raise ValueError(f"Value doesn't fit in the age interval, should be between {values[0]} and {values[1]}")
        else:
            return value

    
class TypeConfValidator(ValidationBaseModel):
    has_age: bool = Field(alias="has_age_range")
    age_range: str | None
    pet_type: str
    weight_range: str
    height_range: str

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, value: str, validated_values: ValidationInfo):
        data = validated_values.data
        if data["has_age"]:
            if '-' in value:
                values = value.split('-')
                if values[0].isdigit() and values[1].isdigit():
                    return value
                else:
                    raise ValueError("One of the values is not an integer")
            else:
                raise ValueError("Value doesn't have the correct separator, should contain '-'")
        else:  
            return None
    
    @field_validator("weight_range")
    @classmethod
    def validate_weight_range(cls, value: str):
        if '-' in value:
            values = value.split('-')
            if values[0].isdigit() and values[1].isdigit():
                return value
            else:
                raise ValueError("One of the values is not an integer")
        else:
            raise ValueError("Value doesn't have the correct separator, should contain '-'")
        
    @field_validator("height_range")
    @classmethod
    def validate_height_range(cls, value: str):
        if '-' in value:
            values = value.split('-')
            if values[0].isdigit() and values[1].isdigit():
                return value
            else:
                raise ValueError("One of the values is not an integer")
        else:
            raise ValueError("Value doesn't have the correct separator, should contain '-'")
        
class PersonConfValidator(ValidationBaseModel):
    pet_lookup: str = Field(validation_alias="ref_table_name1",serialization_alias="ref_table_name1")
    pet_column: str = Field(validation_alias="ref_table_column1",serialization_alias="ref_table_column1")
    pet_id: int
    name: str
    occupation: str = Field(max_length=40)
    nickname: str | None = Field(default=None,max_length=20)

    @field_validator("pet_id")
    @classmethod
    def validate_pet_id(cls, value: int, validated_values: ValidationInfo):
        data = validated_values.data
        if data_exists(data["pet_lookup"],data["pet_column"],value):
            return value
        raise ValueError("Given pet id doesn't exist")