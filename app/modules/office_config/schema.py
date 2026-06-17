from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class ListItem(BaseModel):
    title: str = Field(max_length=200)
    description: str = Field(max_length=1000)


_ListField = Annotated[list[ListItem], Field(max_length=50)]


class OfficeConfigUpdate(BaseModel):
    office_name: str | None = None
    cnpj: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram_url: AnyHttpUrl | None = None
    linkedin_url: AnyHttpUrl | None = None
    whatsapp_url: AnyHttpUrl | None = None

    hero_title: str | None = None
    hero_subtitle: str | None = Field(None, max_length=1000)
    hero_image_url: AnyHttpUrl | None = None

    about_title: str | None = None
    about_description: str | None = Field(None, max_length=5000)
    about_image_url: AnyHttpUrl | None = None

    lawyer_name: str | None = None
    lawyer_oab: str | None = None
    lawyer_description: str | None = Field(None, max_length=5000)
    lawyer_image_url: AnyHttpUrl | None = None

    differentials: _ListField | None = None
    areas_of_practice: _ListField | None = None


class OfficeConfigRead(BaseModel):
    id: int

    office_name: str | None
    cnpj: str | None
    address: str | None
    phone: str | None
    email: str | None
    instagram_url: str | None
    linkedin_url: str | None
    whatsapp_url: str | None

    hero_title: str | None
    hero_subtitle: str | None
    hero_image_url: str | None

    about_title: str | None
    about_description: str | None
    about_image_url: str | None

    lawyer_name: str | None
    lawyer_oab: str | None
    lawyer_description: str | None
    lawyer_image_url: str | None

    differentials: list[ListItem] = []
    areas_of_practice: list[ListItem] = []

    @field_validator("differentials", "areas_of_practice", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v: list | None) -> list:
        return v if v is not None else []

    model_config = ConfigDict(from_attributes=True)
