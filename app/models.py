import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Integer,
    Enum,
    Date,
    Numeric,
    ARRAY,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CAAccount(Base):
    __tablename__ = "ca_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)


client_user_association = Table(
    "client_user_association",
    Base.metadata,
    Column("client_id", UUID(as_uuid=True), ForeignKey("clients.id")),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id")),
)

client_tag_association = Table(
    "client_tag_association",
    Base.metadata,
    Column("client_id", UUID(as_uuid=True), ForeignKey("clients.id")),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id")),
)


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    customer_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    client_type = Column(
        Enum(
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
            name="client_type",
        ),
        nullable=False,
    )
    pan = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    assigned_ca_user_id = Column(UUID(as_uuid=True), ForeignKey("ca_accounts.id"), nullable=True)
    mobile = Column(String, nullable=True)
    secondary_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    opening_balance_amount = Column(Numeric(14, 2), default=0)
    opening_balance_type = Column(
        Enum("debit", "credit", name="opening_balance_type"), nullable=True
    )
    opening_balance_date = Column(Date, nullable=True)
    gst_autofill_enabled = Column(Boolean, default=True)
    gst_last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    can_login = Column(Boolean, default=False)
    notify_client = Column(Boolean, default=True)
    contact_person_name = Column(String, nullable=True)
    contact_person_phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)

    services = relationship("ClientService", back_populates="client", cascade="all, delete-orphan")
    portals = relationship("ClientPortal", back_populates="client", cascade="all, delete-orphan")
    users = relationship("User", secondary=client_user_association, backref="clients")
    tags = relationship("Tag", secondary=client_tag_association, backref="clients")

    __table_args__ = (UniqueConstraint("agency_id", "customer_id", name="uq_agency_id_customer_id"),)


class ClientService(Base):
    __tablename__ = "client_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(UUID(as_uuid=True), nullable=False)

    client = relationship("Client", back_populates="services")

    __table_args__ = (UniqueConstraint("client_id", "service_id", name="uq_client_id_service_id"),)


class AgencySetting(Base):
    __tablename__ = "agency_settings"

    agency_id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id_format = Column(String, nullable=False, default="CLI-{YYYY}-{SEQ4}")
    customer_seq_year = Column(Integer, nullable=False, default=datetime.utcnow().year)
    customer_seq = Column(Integer, nullable=False, default=0)


class Portal(Base):
    __tablename__ = "portals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    login_url = Column(String, nullable=False)


class ClientPortal(Base):
    __tablename__ = "client_portals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    portal_id = Column(UUID(as_uuid=True), ForeignKey("portals.id"), nullable=False)
    username_cipher = Column(String, nullable=True)
    password_cipher = Column(String, nullable=True)
    notes_cipher = Column(String, nullable=True)
    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="portals")
    portal = relationship("Portal")

    @property
    def username_masked(self):
        return f"******{self.username_cipher[-4:]}" if self.username_cipher else ""

    @property
    def username(self):
        return self.username_cipher

    @property
    def password(self):
        return self.password_cipher

    @property
    def notes(self):
        return self.notes_cipher


class GeneralSetting(Base):
    __tablename__ = "general_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    allow_duplicates = Column(Boolean, default=False)
    agency_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = {"extend_existing": True}


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    color = Column(String, nullable=False)


class BusinessType(Base):
    __tablename__ = "business_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
