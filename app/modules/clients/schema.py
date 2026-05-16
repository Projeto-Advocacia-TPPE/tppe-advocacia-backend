from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    cnpj: str | None = Field(default=None, pattern=r"^\d{14}$")
    address: str | None = None

    @model_validator(mode="after")
    def validate_cpf_cnpj(self) -> "ClientCreate":
        has_cpf = self.cpf is not None
        has_cnpj = self.cnpj is not None
        if has_cpf and has_cnpj:
            raise ValueError("CPF e CNPJ não podem ser informados simultaneamente")
        if not has_cpf and not has_cnpj:
            raise ValueError("Informe CPF ou CNPJ")
        return self


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    cnpj: str | None = Field(default=None, pattern=r"^\d{14}$")
    address: str | None = None

    @model_validator(mode="after")
    def validate_cpf_cnpj(self) -> "ClientUpdate":
        if self.cpf is not None and self.cnpj is not None:
            raise ValueError("CPF e CNPJ não podem ser informados simultaneamente")
        return self


class ClientRead(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    cpf: str | None
    cnpj: str | None
    address: str | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientListItem(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    cpf: str | None
    cnpj: str | None

    model_config = ConfigDict(from_attributes=True)
