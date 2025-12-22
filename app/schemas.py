import uuid
import re
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, validator, EmailStr


class ContactInfo(BaseModel):
    mobile: Optional[str] = None
    secondary_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class OpeningBalance(BaseModel):
    amount: float = Field(0.0, ge=0)
    opening_balance_type: Optional[Literal["debit", "credit"]] = None
    opening_balance_date: Optional[date] = None


class ClientServiceLink(BaseModel):
    service_id: uuid.UUID


class ClientServiceRemove(BaseModel):
    service_ids: List[uuid.UUID]


class ClientBase(BaseModel):
    name: str
    client_type: str
    organization_id: Optional[uuid.UUID] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    dob: Optional[date] = None
    assigned_ca_user_id: Optional[uuid.UUID] = None
    tags: List["TagRead"] = []
    gst_autofill_enabled: bool = True
    is_active: bool = True
    can_login: bool = False
    notify_client: bool = True
    contact_person_name: Optional[str] = None
    contact_person_phone: Optional[str] = None
    date_of_birth: Optional[date] = None


    # @validator("pan")
    # def validate_pan(cls, v):
    #     if v and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v):
    #         raise ValueError("Invalid PAN format")
    #     return v.upper() if v else v

    # @validator("gstin")
    # def validate_gstin(cls, v):
    #     if v and len(v) != 15:
    #         raise ValueError("GSTIN must be 15 characters long")
    #     return v.upper() if v else v


class ClientCreate(BaseModel):
    is_active: bool = True
    name: str
    client_type: str
    organization_id: Optional[uuid.UUID] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    contact_person_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    user_ids: List[uuid.UUID] = []
    assigned_ca_user_id: Optional[uuid.UUID] = None
    tag_ids: List[uuid.UUID] = []
    mobile: Optional[str] = None
    secondary_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    opening_balance_date: Optional[date] = None
    opening_balance_amount: float = 0.0
    opening_balance_type: Optional[Literal["debit", "credit"]] = None

    @validator("organization_id", pre=True, always=True)
    def check_organization_id(cls, v, values):
        client_type = values.get("client_type")
        if client_type is not None and client_type != "individual" and v is None:
            raise ValueError("Organization ID is required for non-individual clients")
        return v


class ClientUpdate(ClientBase):
    name: Optional[str] = None
    client_type: Optional[
        Literal[
            "individual",
            "sole_proprietorship",
            "partnership",
            "llp",
            "huf",
            "private_limited",
            "limited_company",
            "joint_venture",
            "one_person_company",
            "ngo",
            "trust",
            "section_8_company",
            "government_entity",
            "cooperative_society",
            "branch_office",
            "aop",
            "society",
        ]
    ] = None
    contact: Optional[ContactInfo] = None
    opening_balance: Optional[OpeningBalance] = None
    services: List[ClientServiceLink] = []
    user_ids: List[uuid.UUID] = []

    @validator("organization_id", pre=True, always=True)
    def check_organization_id(cls, v, values):
        client_type = values.get("client_type")
        if client_type is not None and client_type != "individual" and v is None:
            raise ValueError("Organization ID is required for non-individual clients")
        return v


class UserRead(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class ClientRead(ClientBase):
    id: uuid.UUID
    agency_id: uuid.UUID
    customer_id: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    mobile: Optional[str]
    secondary_phone: Optional[str]
    email: Optional[EmailStr]
    photo_url: Optional[str] = None
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    opening_balance_amount: float
    opening_balance_type: Optional[Literal["debit", "credit"]]
    opening_balance_date: Optional[date] = None
    users: List[UserRead] = []
    tags: List["TagRead"] = []

    class Config:
        from_attributes = True


class ClientPortalBase(BaseModel):
    portal_id: uuid.UUID
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None


class ClientPortalCreate(ClientPortalBase):
    pass


class ClientPortalUpdate(ClientPortalBase):
    portal_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None


class PortalBase(BaseModel):
    name: str
    login_url: str


class PortalCreate(PortalBase):
    pass


class PortalUpdate(PortalBase):
    name: Optional[str] = None
    login_url: Optional[str] = None


class PortalRead(PortalBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class GeneralSettingBase(BaseModel):
    allow_duplicates: bool = False


class GeneralSettingCreate(GeneralSettingBase):
    pass


class GeneralSettingUpdate(GeneralSettingBase):
    pass


class GeneralSettingRead(GeneralSettingBase):
    id: uuid.UUID
    agency_id: uuid.UUID
    created_by: uuid.UUID
    updated_at: datetime

    class Config:
        from_attributes = True


class TagBase(BaseModel):
    name: str
    color: str


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    name: Optional[str] = None
    color: Optional[str] = None


class TagRead(TagBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class BusinessTypeBase(BaseModel):
    name: str


class BusinessTypeCreate(BusinessTypeBase):
    pass


class BusinessTypeUpdate(BusinessTypeBase):
    name: Optional[str] = None


class BusinessTypeRead(BusinessTypeBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class ClientPortalRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    portal: PortalRead
    username_masked: str
    last_rotated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientPortalWithSecrets(ClientPortalRead):
    username: str
    password: str
    notes: Optional[str]


class ClientPortalSecret(BaseModel):
    username: str
    password: str
    notes: Optional[str]


class ClientDashboard(BaseModel):
    is_active: bool
    client_type: str
    contact_person_name: Optional[str]
    date_of_birth: Optional[date]
    pan: Optional[str]
    mobile: Optional[str]
    email: Optional[EmailStr]
    city: Optional[str]
    postal_code: Optional[str]
    state: Optional[str]

    class Config:
        from_attributes = True


class InviteUser(BaseModel):
    org_id: uuid.UUID
    email: EmailStr


class LedgerBalance(BaseModel):
    opening_balance_amount: float

    class Config:
        from_attributes = True
