from pydantic import BaseModel, ConfigDict, field_validator


class ListItem(BaseModel):
    title: str
    description: str


class OfficeConfigUpdate(BaseModel):
    office_name: str | None = None
    cnpj: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    linkedin_url: str | None = None
    whatsapp_url: str | None = None

    hero_title: str | None = None
    hero_subtitle: str | None = None
    hero_image_url: str | None = None

    about_title: str | None = None
    about_description: str | None = None
    about_image_url: str | None = None

    lawyer_name: str | None = None
    lawyer_oab: str | None = None
    lawyer_description: str | None = None
    lawyer_image_url: str | None = None

    differentials: list[ListItem] | None = None
    areas_of_practice: list[ListItem] | None = None


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
