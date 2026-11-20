from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator

from modules.inaproc.api.spt import SptNumber

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_delay(delay_min: float, delay_max: float) -> None:
    if delay_min <= 0 or delay_max < delay_min:
        raise ValueError("delay_tidak_valid: delay_min must be positive and delay_max must be at least delay_min")
    if delay_max > 30:
        raise ValueError("delay_tidak_valid: delay_max must be at most 30")

class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("email is not valid")
        return value

class LookupRequest(BaseModel):
    model_config = {"populate_by_name": True}

    number: str = Field(validation_alias=AliasChoices("number", "nomor"))
    force: bool = False

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: str) -> str:
        value = value.strip()
        try:
            SptNumber.parse(value)
        except ValueError as exc:
            raise ValueError(f"nomor_tidak_valid: {exc}") from exc
        return value

class CollectRequest(BaseModel):
    model_config = {"populate_by_name": True}

    template: str = Field(validation_alias=AliasChoices("template", "nomor"))
    start: int
    end: int
    delay_min: float = 1.0
    delay_max: float = 3.0
    force: bool = False

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        value = value.strip()
        try:
            SptNumber.parse(value)
        except ValueError as exc:
            raise ValueError(f"nomor_tidak_valid: {exc}") from exc
        return value

    @model_validator(mode="after")
    def validate_range(self):
        if self.start > self.end:
            raise ValueError("rentang_tidak_valid: start must be less than or equal to end")
        if self.end - self.start + 1 > 1000:
            raise ValueError("rentang_terlalu_besar: a single collect request is limited to 1000 numbers")
        validate_delay(self.delay_min, self.delay_max)
        return self

class PreviewRequest(BaseModel):
    model_config = {"populate_by_name": True}

    template: str = Field(validation_alias=AliasChoices("template", "nomor"))
    start: int
    end: int
    delay_min: float = 1.0
    delay_max: float = 3.0

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        value = value.strip()
        try:
            SptNumber.parse(value)
        except ValueError as exc:
            raise ValueError(f"nomor_tidak_valid: {exc}") from exc
        return value

    @model_validator(mode="after")
    def validate_range(self):
        if self.start > self.end:
            raise ValueError("rentang_tidak_valid: start must be less than or equal to end")
        validate_delay(self.delay_min, self.delay_max)
        return self

class RefreshRequest(BaseModel):
    model_config = {"populate_by_name": True}

    number: str = Field(validation_alias=AliasChoices("number", "nomor"))

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: str) -> str:
        value = value.strip()
        try:
            SptNumber.parse(value)
        except ValueError as exc:
            raise ValueError(f"nomor_tidak_valid: {exc}") from exc
        return value

class SearchParams(BaseModel):
    q: str = ""
    brand: str | None = None
    min_value: float | None = None
    page: int = 1
    per_page: int = 50
    sort: Literal["number", "brand", "value", "product_type"] = "number"
    order: Literal["asc", "desc"] = "asc"
