from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'loadflow.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "loadflow-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8
PERMISSION_CATALOG = [
    "load.create",
    "load.assign_carrier",
    "load.override_compliance_flag",
    "rate.confirm",
    "load.update_status",
    "staff.manage",
    "pod.upload",
]
LOAD_ORDER = [
    "Posted",
    "Carrier Assigned",
    "Rate Confirmed",
    "Dispatched",
    "In Transit",
    "Delivered",
    "POD Verified",
    "Invoiced/Closed",
]
UPLOAD_DIR = BASE_DIR / "uploads" / "pod"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Base(DeclarativeBase):
    pass


role_permissions = Base.metadata.tables.get("role_permissions")
from sqlalchemy import Table, Column

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(back_populates="organization")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(String(200))


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_role_org_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(80))
    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions)
    organization: Mapped[Organization] = relationship(back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(20))
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped[Organization | None] = relationship(back_populates="users")
    role: Mapped[Role | None] = relationship()
    roles: Mapped[list[Role]] = relationship(secondary=user_roles)


class ComplianceRecord(Base):
    __tablename__ = "carrier_compliance"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), unique=True)
    insurance_expiry: Mapped[date] = mapped_column(Date)
    authority_status: Mapped[str] = mapped_column(String(30))
    approved_equipment: Mapped[str] = mapped_column(Text, default="[]")
    approved_commodities: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    broker_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    shipper_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    carrier_org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    origin: Mapped[str] = mapped_column(String(160))
    destination: Mapped[str] = mapped_column(String(160))
    equipment_type: Mapped[str] = mapped_column(String(80))
    commodity: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="Posted")
    compliance_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_rate_confirmation_id: Mapped[int | None] = mapped_column(ForeignKey("rate_confirmation_versions.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RateConfirmation(Base):
    __tablename__ = "rate_confirmation_versions"
    __table_args__ = (UniqueConstraint("load_id", "version", name="uq_load_rate_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    load_id: Mapped[int] = mapped_column(ForeignKey("loads.id"))
    carrier_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    version: Mapped[int] = mapped_column(Integer)
    base_rate: Mapped[float] = mapped_column(Float)
    accessorials: Mapped[str] = mapped_column(Text, default="[]")
    confirmed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Pod(Base):
    __tablename__ = "pod_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    load_id: Mapped[int] = mapped_column(ForeignKey("loads.id"), unique=True)
    file_name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    verified_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoadStatusHistory(Base):
    __tablename__ = "load_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    load_id: Mapped[int] = mapped_column(ForeignKey("loads.id"))
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40))
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class BootstrapAdmin(BaseModel):
    organization_name: str
    organization_type: Literal["broker", "carrier"]
    name: str
    email: str
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: str
    password: str


class RoleIn(BaseModel):
    name: str
    permissions: list[str]


class StaffIn(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    role_id: int


class LoadIn(BaseModel):
    reference: str
    shipper_user_id: int
    origin: str
    destination: str
    equipment_type: str
    commodity: str


class LoadPatch(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    commodity: str | None = None


class AssignCarrierIn(BaseModel):
    carrier_org_id: int


class StatusIn(BaseModel):
    status: str


class CarrierDecisionIn(BaseModel):
    decision: Literal["accepted", "declined"]


class ComplianceIn(BaseModel):
    carrier_org_id: int
    insurance_expiry: date
    authority_status: Literal["active", "lapsed", "pending"]
    approved_equipment: list[str]
    approved_commodities: list[str]


class RateIn(BaseModel):
    base_rate: float = Field(gt=0)
    accessorials: list[dict[str, Any]] = []


class ShipperIn(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def user_payload(user: User) -> dict[str, Any]:
    permissions = sorted(get_user_permissions(user))
    role_names = [role.name for role in user.roles] or ([user.role.name] if user.role else [])
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "account_type": user.account_type,
        "organization_id": user.organization_id,
        "organization_name": user.organization.name if user.organization else None,
        "is_admin": user.is_admin,
        "role": ", ".join(role_names) if role_names else ("Admin" if user.is_admin else None),
        "roles": role_names,
        "permissions": permissions,
    }


def get_user_permissions(user: User) -> set[str]:
    if user.account_type in {"broker", "carrier"} and user.is_admin:
        return set(PERMISSION_CATALOG)
    if user.roles:
        return {permission.code for role in user.roles for permission in role.permissions}
    if user.role:
        return {permission.code for permission in user.role.permissions}
    return set()


def log_event(db: Session, user: User | None, action: str, entity_type: str, entity_id: int | None = None, details: dict[str, Any] | None = None) -> None:
    db.add(
        AuditEvent(
            user_id=user.id if user else None,
            organization_id=user.organization_id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}),
        )
    )


def record_status_history(db: Session, load: Load, from_status: str | None, to_status: str, user: User | None, note: str | None = None) -> None:
    db.add(
        LoadStatusHistory(
            load_id=load.id,
            from_status=from_status,
            to_status=to_status,
            changed_by_user_id=user.id if user else None,
            note=note,
        )
    )


def deny(db: Session, user: User | None, action: str, entity_type: str = "permission", entity_id: int | None = None) -> None:
    print(f"PERMISSION_DENIED user={user.email if user else 'anonymous'} action={action} entity={entity_type}:{entity_id}")
    log_event(db, user, "permission_denied", entity_type, entity_id, {"attempted": action})
    db.commit()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


def require_permission(db: Session, user: User, permission: str) -> None:
    if permission not in get_user_permissions(user):
        deny(db, user, permission)


def current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def load_for_user(db: Session, user: User, load_id: int) -> Load:
    load = db.get(Load, load_id)
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    if user.account_type == "broker" and load.broker_org_id == user.organization_id:
        return load
    if user.account_type == "carrier" and load.carrier_org_id == user.organization_id:
        return load
    if user.account_type == "shipper" and load.shipper_user_id == user.id:
        return load
    deny(db, user, "object_scope.load", "load", load_id)


def apply_compliance(db: Session, load: Load, carrier_org_id: int) -> None:
    compliance = db.scalar(select(ComplianceRecord).where(ComplianceRecord.carrier_org_id == carrier_org_id))
    reasons: list[str] = []
    if not compliance:
        reasons.append("missing compliance record")
    else:
        equipment = json.loads(compliance.approved_equipment)
        commodities = json.loads(compliance.approved_commodities)
        if compliance.insurance_expiry < date.today():
            reasons.append("insurance expired")
        if compliance.authority_status != "active":
            reasons.append(f"authority {compliance.authority_status}")
        if load.equipment_type not in equipment:
            reasons.append("equipment not approved")
        if load.commodity not in commodities:
            reasons.append("commodity not approved")
    load.compliance_flag = bool(reasons)
    load.compliance_reason = "; ".join(reasons) if reasons else None


def transition(load: Load, target: str, db: Session | None = None, user: User | None = None, note: str | None = None) -> None:
    if target not in LOAD_ORDER:
        raise HTTPException(status_code=400, detail="Unknown load status")
    current_index = LOAD_ORDER.index(load.status)
    target_index = LOAD_ORDER.index(target)
    if target_index != current_index + 1:
        raise HTTPException(status_code=400, detail=f"Invalid transition from {load.status} to {target}")
    if load.compliance_flag and target_index > LOAD_ORDER.index("Carrier Assigned"):
        raise HTTPException(status_code=409, detail="Compliance flag blocks progression past Carrier Assigned")
    previous = load.status
    load.status = target
    load.updated_at = datetime.utcnow()
    if db is not None:
        record_status_history(db, load, previous, target, user, note)


def seed_permissions(db: Session) -> None:
    for code in PERMISSION_CATALOG:
        if not db.scalar(select(Permission).where(Permission.code == code)):
            db.add(Permission(code=code, description=code.replace(".", " ").title()))


def get_or_create_org(db: Session, name: str, organization_type: str) -> Organization:
    org = db.scalar(select(Organization).where(Organization.name == name))
    if org:
        return org
    org = Organization(name=name, type=organization_type)
    db.add(org)
    db.flush()
    return org


def get_or_create_role(db: Session, organization_id: int, name: str, permission_codes: list[str]) -> Role:
    role = db.scalar(select(Role).where(Role.organization_id == organization_id, Role.name == name))
    if role:
        return role
    permissions = {permission.code: permission for permission in db.scalars(select(Permission)).all()}
    role = Role(organization_id=organization_id, name=name, permissions=[permissions[code] for code in permission_codes])
    db.add(role)
    db.flush()
    return role


def get_or_create_user(
    db: Session,
    *,
    email: str,
    name: str,
    account_type: str,
    organization_id: int | None = None,
    role: Role | None = None,
    is_admin: bool = False,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        if role and role not in user.roles:
            user.roles.append(role)
        return user
    user = User(
        email=email,
        name=name,
        password_hash=hash_password("Password123"),
        account_type=account_type,
        organization_id=organization_id,
        role_id=role.id if role else None,
        roles=[role] if role else [],
        is_admin=is_admin,
    )
    db.add(user)
    db.flush()
    return user


def upsert_compliance_seed(
    db: Session,
    *,
    carrier_org_id: int,
    insurance_expiry: date,
    authority_status: str,
    approved_equipment: list[str],
    approved_commodities: list[str],
) -> ComplianceRecord:
    record = db.scalar(select(ComplianceRecord).where(ComplianceRecord.carrier_org_id == carrier_org_id))
    values = {
        "insurance_expiry": insurance_expiry,
        "authority_status": authority_status,
        "approved_equipment": json.dumps(approved_equipment),
        "approved_commodities": json.dumps(approved_commodities),
        "updated_at": datetime.utcnow(),
    }
    if record:
        for key, value in values.items():
            setattr(record, key, value)
    else:
        record = ComplianceRecord(carrier_org_id=carrier_org_id, **values)
        db.add(record)
    db.flush()
    return record


def add_history_if_empty(db: Session, load: Load, user: User, statuses: list[str]) -> None:
    exists = db.scalar(select(LoadStatusHistory).where(LoadStatusHistory.load_id == load.id))
    if exists:
        return
    previous: str | None = None
    for status_name in statuses:
        record_status_history(db, load, previous, status_name, user, "Seeded workflow timeline")
        previous = status_name


def add_rate_version_if_missing(db: Session, load: Load, carrier_org_id: int, user: User, version: int, base_rate: float, accessorials: list[dict[str, Any]]) -> RateConfirmation:
    rate = db.scalar(select(RateConfirmation).where(RateConfirmation.load_id == load.id, RateConfirmation.version == version))
    if rate:
        return rate
    rate = RateConfirmation(
        load_id=load.id,
        carrier_org_id=carrier_org_id,
        version=version,
        base_rate=base_rate,
        accessorials=json.dumps(accessorials),
        confirmed_by_user_id=user.id,
    )
    db.add(rate)
    db.flush()
    return rate


def get_or_create_load(
    db: Session,
    *,
    reference: str,
    broker_org_id: int,
    shipper_user_id: int,
    created_by_id: int,
    origin: str,
    destination: str,
    equipment_type: str,
    commodity: str,
    status: str = "Posted",
    carrier_org_id: int | None = None,
) -> Load:
    load = db.scalar(select(Load).where(Load.reference == reference))
    if load:
        return load
    load = Load(
        reference=reference,
        broker_org_id=broker_org_id,
        shipper_user_id=shipper_user_id,
        carrier_org_id=carrier_org_id,
        origin=origin,
        destination=destination,
        equipment_type=equipment_type,
        commodity=commodity,
        status=status,
        created_by_id=created_by_id,
    )
    if carrier_org_id:
        apply_compliance(db, load, carrier_org_id)
    db.add(load)
    db.flush()
    return load


def seed_expanded_demo(db: Session) -> None:
    seed_permissions(db)
    broker = get_or_create_org(db, "Blue River Brokerage", "broker")
    northstar = get_or_create_org(db, "Northstar Carrier", "carrier")
    prairie = get_or_create_org(db, "Prairie Logistics", "carrier")

    dispatcher = get_or_create_role(db, broker.id, "Dispatcher", ["load.assign_carrier", "rate.confirm", "load.update_status"])
    ops_lead = get_or_create_role(db, broker.id, "Ops Lead", PERMISSION_CATALOG)
    billing = get_or_create_role(db, broker.id, "Billing Clerk", ["load.update_status"])
    driver = get_or_create_role(db, northstar.id, "Driver", ["load.update_status", "pod.upload"])
    carrier_dispatch = get_or_create_role(db, northstar.id, "Carrier Dispatch", ["load.update_status", "staff.manage"])
    pod_clerk = get_or_create_role(db, prairie.id, "POD Clerk", ["pod.upload", "load.update_status"])

    broker_admin = get_or_create_user(db, email="broker.admin@loadflow.test", name="Brenda Broker", account_type="broker", organization_id=broker.id, is_admin=True)
    dispatcher_user = get_or_create_user(db, email="dispatcher@loadflow.test", name="Dina Dispatcher", account_type="broker", organization_id=broker.id, role=dispatcher)
    ops_user = get_or_create_user(db, email="ops.lead@loadflow.test", name="Owen Ops", account_type="broker", organization_id=broker.id, role=ops_lead)
    billing_user = get_or_create_user(db, email="billing@loadflow.test", name="Bianca Billing", account_type="broker", organization_id=broker.id, role=billing)
    carrier_admin = get_or_create_user(db, email="carrier.admin@loadflow.test", name="Carlos Carrier", account_type="carrier", organization_id=northstar.id, is_admin=True)
    driver_user = get_or_create_user(db, email="driver@loadflow.test", name="Dev Driver", account_type="carrier", organization_id=northstar.id, role=driver)
    dispatch_user = get_or_create_user(db, email="carrier.dispatch@loadflow.test", name="Casey Dispatch", account_type="carrier", organization_id=northstar.id, role=carrier_dispatch)
    prairie_user = get_or_create_user(db, email="prairie.pod@loadflow.test", name="Priya POD", account_type="carrier", organization_id=prairie.id, role=pod_clerk)
    shipper_user = get_or_create_user(db, email="shipper@loadflow.test", name="Sam Shipper", account_type="shipper")
    foods_shipper = get_or_create_user(db, email="evergreen.foods@loadflow.test", name="Evergreen Foods", account_type="shipper")
    retail_shipper = get_or_create_user(db, email="metro.retail@loadflow.test", name="Metro Retail", account_type="shipper")

    upsert_compliance_seed(
        db,
        carrier_org_id=northstar.id,
        insurance_expiry=date.today() + timedelta(days=45),
        authority_status="active",
        approved_equipment=["Dry Van", "Reefer"],
        approved_commodities=["Food", "Retail"],
    )
    upsert_compliance_seed(
        db,
        carrier_org_id=prairie.id,
        insurance_expiry=date.today() - timedelta(days=5),
        authority_status="lapsed",
        approved_equipment=["Flatbed"],
        approved_commodities=["Steel"],
    )

    posted = get_or_create_load(
        db,
        reference="LF-1002",
        broker_org_id=broker.id,
        shipper_user_id=retail_shipper.id,
        created_by_id=dispatcher_user.id,
        origin="Columbus, OH",
        destination="Charlotte, NC",
        equipment_type="Dry Van",
        commodity="Retail",
    )
    add_history_if_empty(db, posted, dispatcher_user, ["Posted"])

    rate_confirmed = get_or_create_load(
        db,
        reference="LF-1003",
        broker_org_id=broker.id,
        shipper_user_id=foods_shipper.id,
        carrier_org_id=northstar.id,
        created_by_id=broker_admin.id,
        origin="Omaha, NE",
        destination="Denver, CO",
        equipment_type="Reefer",
        commodity="Food",
        status="Rate Confirmed",
    )
    rate1 = add_rate_version_if_missing(db, rate_confirmed, northstar.id, broker_admin, 1, 2850, [{"name": "Fuel surcharge", "amount": 175}])
    rate2 = add_rate_version_if_missing(db, rate_confirmed, northstar.id, broker_admin, 2, 2975, [{"name": "Fuel surcharge", "amount": 185}, {"name": "Lumper", "amount": 90}])
    rate_confirmed.current_rate_confirmation_id = rate2.id
    add_history_if_empty(db, rate_confirmed, broker_admin, ["Posted", "Carrier Assigned", "Rate Confirmed"])

    in_transit = get_or_create_load(
        db,
        reference="LF-1004",
        broker_org_id=broker.id,
        shipper_user_id=shipper_user.id,
        carrier_org_id=northstar.id,
        created_by_id=ops_user.id,
        origin="Kansas City, MO",
        destination="Phoenix, AZ",
        equipment_type="Dry Van",
        commodity="Retail",
        status="In Transit",
    )
    in_transit_rate = add_rate_version_if_missing(db, in_transit, northstar.id, ops_user, 1, 3350, [{"name": "Team service", "amount": 350}])
    in_transit.current_rate_confirmation_id = in_transit_rate.id
    add_history_if_empty(db, in_transit, driver_user, ["Posted", "Carrier Assigned", "Rate Confirmed", "Dispatched", "In Transit"])

    delivered = get_or_create_load(
        db,
        reference="LF-1005",
        broker_org_id=broker.id,
        shipper_user_id=foods_shipper.id,
        carrier_org_id=northstar.id,
        created_by_id=ops_user.id,
        origin="Fresno, CA",
        destination="Portland, OR",
        equipment_type="Reefer",
        commodity="Food",
        status="Delivered",
    )
    delivered_rate = add_rate_version_if_missing(db, delivered, northstar.id, ops_user, 1, 1900, [{"name": "Detention", "amount": 125}])
    delivered.current_rate_confirmation_id = delivered_rate.id
    add_history_if_empty(db, delivered, driver_user, ["Posted", "Carrier Assigned", "Rate Confirmed", "Dispatched", "In Transit", "Delivered"])
    if not db.scalar(select(Pod).where(Pod.load_id == delivered.id)):
        pod_path = UPLOAD_DIR / "seed-lf-1005-pod.txt"
        pod_path.write_text("Seed POD for LF-1005\nDelivered clean and complete.\n", encoding="utf-8")
        db.add(Pod(load_id=delivered.id, file_name="seed-lf-1005-pod.txt", url=str(pod_path.relative_to(BASE_DIR)).replace("\\", "/"), uploaded_by_user_id=driver_user.id))

    flagged = get_or_create_load(
        db,
        reference="LF-1006",
        broker_org_id=broker.id,
        shipper_user_id=retail_shipper.id,
        carrier_org_id=prairie.id,
        created_by_id=dispatcher_user.id,
        origin="Pittsburgh, PA",
        destination="Atlanta, GA",
        equipment_type="Flatbed",
        commodity="Steel",
        status="Carrier Assigned",
    )
    apply_compliance(db, flagged, prairie.id)
    add_history_if_empty(db, flagged, dispatcher_user, ["Posted", "Carrier Assigned"])

    closed = get_or_create_load(
        db,
        reference="LF-1007",
        broker_org_id=broker.id,
        shipper_user_id=shipper_user.id,
        carrier_org_id=northstar.id,
        created_by_id=billing_user.id,
        origin="Memphis, TN",
        destination="Nashville, TN",
        equipment_type="Dry Van",
        commodity="Retail",
        status="Invoiced/Closed",
    )
    closed_rate = add_rate_version_if_missing(db, closed, northstar.id, billing_user, 1, 850, [])
    closed.current_rate_confirmation_id = closed_rate.id
    add_history_if_empty(db, closed, billing_user, ["Posted", "Carrier Assigned", "Rate Confirmed", "Dispatched", "In Transit", "Delivered", "POD Verified", "Invoiced/Closed"])

    notification_specs = [
        (broker.id, None, "compliance_flag", "LF-1006 is blocked by Prairie Logistics compliance."),
        (northstar.id, carrier_admin.id, "insurance_renewal", "Northstar insurance renewal is due within 45 days."),
        (prairie.id, prairie_user.id, "authority_lapsed", "Prairie Logistics authority is lapsed; update before dispatch."),
    ]
    for organization_id, user_id, notification_type, message in notification_specs:
        exists = db.scalar(select(Notification).where(Notification.organization_id == organization_id, Notification.type == notification_type, Notification.message == message))
        if not exists:
            db.add(Notification(organization_id=organization_id, user_id=user_id, type=notification_type, message=message))

    audit_specs = [
        (broker_admin, "seed.expanded_demo", "system", None, {"loads": 6}),
        (dispatcher_user, "load.create", "load", posted.id, {"reference": posted.reference}),
        (ops_user, "rate.confirm", "load", rate_confirmed.id, {"version": 2}),
        (driver_user, "load.update_status", "load", in_transit.id, {"status": "In Transit"}),
        (prairie_user, "permission_denied", "load", flagged.id, {"attempted": "dispatch while noncompliant"}),
    ]
    for actor, action, entity_type, entity_id, details in audit_specs:
        exists = db.scalar(select(AuditEvent).where(AuditEvent.action == action, AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id))
        if not exists:
            log_event(db, actor, action, entity_type, entity_id, details)


def seed_demo(db: Session) -> None:
    seed_permissions(db)
    if db.scalar(select(User).where(User.email == "broker.admin@loadflow.test")):
        seed_expanded_demo(db)
        db.commit()
        return
    broker = Organization(name="Blue River Brokerage", type="broker")
    carrier = Organization(name="Northstar Carrier", type="carrier")
    db.add_all([broker, carrier])
    db.flush()
    permissions = {p.code: p for p in db.scalars(select(Permission)).all()}
    dispatcher = Role(organization_id=broker.id, name="Dispatcher", permissions=[permissions["load.assign_carrier"], permissions["rate.confirm"], permissions["load.update_status"]])
    ops_lead = Role(organization_id=broker.id, name="Ops Lead", permissions=list(permissions.values()))
    driver = Role(organization_id=carrier.id, name="Driver", permissions=[permissions["load.update_status"], permissions["pod.upload"]])
    carrier_dispatch = Role(organization_id=carrier.id, name="Carrier Dispatch", permissions=[permissions["load.update_status"]])
    db.add_all([dispatcher, ops_lead, driver, carrier_dispatch])
    db.flush()
    users = [
        User(email="broker.admin@loadflow.test", name="Brenda Broker", password_hash=hash_password("Password123"), account_type="broker", organization_id=broker.id, is_admin=True),
        User(email="dispatcher@loadflow.test", name="Dina Dispatcher", password_hash=hash_password("Password123"), account_type="broker", organization_id=broker.id, role_id=dispatcher.id, roles=[dispatcher]),
        User(email="carrier.admin@loadflow.test", name="Carlos Carrier", password_hash=hash_password("Password123"), account_type="carrier", organization_id=carrier.id, is_admin=True),
        User(email="driver@loadflow.test", name="Dev Driver", password_hash=hash_password("Password123"), account_type="carrier", organization_id=carrier.id, role_id=driver.id, roles=[driver]),
        User(email="shipper@loadflow.test", name="Sam Shipper", password_hash=hash_password("Password123"), account_type="shipper"),
    ]
    db.add_all(users)
    db.flush()
    db.add(
        ComplianceRecord(
            carrier_org_id=carrier.id,
            insurance_expiry=date.today() + timedelta(days=45),
            authority_status="active",
            approved_equipment=json.dumps(["Dry Van", "Reefer"]),
            approved_commodities=json.dumps(["Food", "Retail"]),
        )
    )
    good = Load(
        reference="LF-1001",
        broker_org_id=broker.id,
        shipper_user_id=users[-1].id,
        carrier_org_id=carrier.id,
        origin="Chicago, IL",
        destination="Dallas, TX",
        equipment_type="Dry Van",
        commodity="Retail",
        status="Carrier Assigned",
        created_by_id=users[0].id,
    )
    apply_compliance(db, good, carrier.id)
    db.add(good)
    db.flush()
    record_status_history(db, good, None, good.status, users[0], "Seeded demo load")
    log_event(db, users[0], "seed_demo", "system", None, {"demo_password": "Password123"})
    seed_expanded_demo(db)
    db.commit()


def init_app_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo(db)


if os.getenv("LOADFLOW_SKIP_AUTO_INIT") != "1":
    init_app_database()

app = FastAPI(title="LoadFlow API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=BASE_DIR / "uploads"), name="uploads")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/bootstrap/admin", response_model=Token)
def bootstrap_admin(payload: BootstrapAdmin, db: Annotated[Session, Depends(get_db)]) -> Token:
    seed_permissions(db)
    existing_admin = db.scalar(
        select(User)
        .join(Organization, User.organization_id == Organization.id)
        .where(Organization.type == payload.organization_type, User.is_admin.is_(True))
    )
    if existing_admin:
        raise HTTPException(status_code=409, detail=f"First {payload.organization_type} admin already exists; invite staff through staff management")
    org = Organization(name=payload.organization_name, type=payload.organization_type)
    db.add(org)
    db.flush()
    user = User(
        email=payload.email.lower(),
        name=payload.name,
        password_hash=hash_password(payload.password),
        account_type=payload.organization_type,
        organization_id=org.id,
        is_admin=True,
    )
    db.add(user)
    log_event(db, user, "bootstrap_admin", "organization", org.id)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_token(user), user=user_payload(user))


@app.post("/api/v1/auth/login", response_model=Token)
def login(payload: LoginIn, db: Annotated[Session, Depends(get_db)]) -> Token:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_token(user), user=user_payload(user))


@app.get("/api/v1/auth/me")
def me(user: Annotated[User, Depends(current_user)]) -> dict[str, Any]:
    return user_payload(user)


@app.get("/api/v1/permissions")
def permissions(_: Annotated[User, Depends(current_user)]) -> list[dict[str, str]]:
    return [{"code": code, "description": code.replace(".", " ").title()} for code in PERMISSION_CATALOG]


@app.get("/api/v1/organizations")
def organizations(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)], type: str | None = None) -> list[dict[str, Any]]:
    stmt = select(Organization)
    if type:
        stmt = stmt.where(Organization.type == type)
    if user.account_type == "carrier":
        stmt = stmt.where(Organization.id == user.organization_id)
    elif user.account_type == "broker" and type != "carrier":
        stmt = stmt.where(Organization.id == user.organization_id)
    return [{"id": org.id, "name": org.name, "type": org.type} for org in db.scalars(stmt).all()]


@app.get("/api/v1/roles")
def list_roles(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    if user.account_type == "shipper":
        deny(db, user, "staff.manage")
    roles = db.scalars(select(Role).where(Role.organization_id == user.organization_id)).all()
    return [{"id": r.id, "name": r.name, "permissions": [p.code for p in r.permissions]} for r in roles]


@app.post("/api/v1/roles")
def create_role(payload: RoleIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "staff.manage")
    invalid = set(payload.permissions) - set(PERMISSION_CATALOG)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {sorted(invalid)}")
    permission_rows = db.scalars(select(Permission).where(Permission.code.in_(payload.permissions))).all()
    role = Role(organization_id=user.organization_id, name=payload.name, permissions=permission_rows)
    db.add(role)
    log_event(db, user, "role.create", "role", None, payload.model_dump())
    db.commit()
    db.refresh(role)
    return {"id": role.id, "name": role.name, "permissions": [p.code for p in role.permissions]}


@app.post("/api/v1/users/staff")
def create_staff(payload: StaffIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "staff.manage")
    role = db.get(Role, payload.role_id)
    if not role or role.organization_id != user.organization_id:
        raise HTTPException(status_code=400, detail="Role must belong to your organization")
    staff = User(
        email=payload.email.lower(),
        name=payload.name,
        password_hash=hash_password(payload.password),
        account_type=user.account_type,
        organization_id=user.organization_id,
        role_id=role.id,
        roles=[role],
    )
    db.add(staff)
    log_event(db, user, "staff.create", "user", None, {"email": payload.email, "role_id": role.id})
    db.commit()
    db.refresh(staff)
    return user_payload(staff)


@app.post("/api/v1/users/shippers")
def create_shipper(payload: ShipperIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.create")
    if user.account_type != "broker":
        deny(db, user, "shipper.create")
    shipper = User(email=payload.email.lower(), name=payload.name, password_hash=hash_password(payload.password), account_type="shipper")
    db.add(shipper)
    log_event(db, user, "shipper.create", "user", None, {"email": payload.email})
    db.commit()
    return user_payload(shipper)


@app.get("/api/v1/users/shippers")
def list_shippers(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    if user.account_type != "broker":
        deny(db, user, "shipper.list")
    return [user_payload(s) for s in db.scalars(select(User).where(User.account_type == "shipper")).all()]


@app.get("/api/v1/compliance")
def list_compliance(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    stmt = select(ComplianceRecord)
    if user.account_type == "carrier":
        stmt = stmt.where(ComplianceRecord.carrier_org_id == user.organization_id)
    rows = db.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "carrier_org_id": row.carrier_org_id,
            "insurance_expiry": row.insurance_expiry.isoformat(),
            "authority_status": row.authority_status,
            "approved_equipment": json.loads(row.approved_equipment),
            "approved_commodities": json.loads(row.approved_commodities),
        }
        for row in rows
    ]


@app.post("/api/v1/compliance")
def upsert_compliance(payload: ComplianceIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "staff.manage")
    if user.account_type == "carrier" and payload.carrier_org_id != user.organization_id:
        deny(db, user, "object_scope.compliance")
    if user.account_type == "shipper":
        deny(db, user, "compliance.manage")
    record = db.scalar(select(ComplianceRecord).where(ComplianceRecord.carrier_org_id == payload.carrier_org_id))
    values = {
        "insurance_expiry": payload.insurance_expiry,
        "authority_status": payload.authority_status,
        "approved_equipment": json.dumps(payload.approved_equipment),
        "approved_commodities": json.dumps(payload.approved_commodities),
        "updated_at": datetime.utcnow(),
    }
    if record:
        for key, value in values.items():
            setattr(record, key, value)
    else:
        record = ComplianceRecord(carrier_org_id=payload.carrier_org_id, **values)
        db.add(record)
    for load in db.scalars(select(Load).where(Load.carrier_org_id == payload.carrier_org_id)).all():
        apply_compliance(db, load, payload.carrier_org_id)
    log_event(db, user, "compliance.upsert", "compliance", payload.carrier_org_id, payload.model_dump(mode="json"))
    db.commit()
    return {"ok": True}


@app.delete("/api/v1/compliance/{carrier_org_id}", status_code=204)
def delete_compliance(carrier_org_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> None:
    require_permission(db, user, "staff.manage")
    if user.account_type == "carrier" and carrier_org_id != user.organization_id:
        deny(db, user, "object_scope.compliance")
    if user.account_type == "shipper":
        deny(db, user, "compliance.manage")
    record = db.scalar(select(ComplianceRecord).where(ComplianceRecord.carrier_org_id == carrier_org_id))
    if not record:
        raise HTTPException(status_code=404, detail="Compliance record not found")
    db.delete(record)
    for load in db.scalars(select(Load).where(Load.carrier_org_id == carrier_org_id)).all():
        load.compliance_flag = True
        load.compliance_reason = "missing compliance record"
    log_event(db, user, "compliance.delete", "compliance", carrier_org_id)
    db.commit()
    return None


@app.get("/api/v1/loads")
def list_loads(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[dict[str, Any]]:
    stmt = select(Load)
    if user.account_type == "broker":
        stmt = stmt.where(Load.broker_org_id == user.organization_id)
    elif user.account_type == "carrier":
        stmt = stmt.where(Load.carrier_org_id == user.organization_id)
    else:
        stmt = stmt.where(Load.shipper_user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Load.reference.like(like)) | (Load.origin.like(like)) | (Load.destination.like(like)) | (Load.commodity.like(like)))
    if status_filter:
        stmt = stmt.where(Load.status == status_filter)
    return [serialize_load(db, load) for load in db.scalars(stmt.order_by(Load.created_at.desc())).all()]


def serialize_load(db: Session, load: Load) -> dict[str, Any]:
    carrier = db.get(Organization, load.carrier_org_id) if load.carrier_org_id else None
    shipper = db.get(User, load.shipper_user_id)
    rate = db.get(RateConfirmation, load.current_rate_confirmation_id) if load.current_rate_confirmation_id else None
    pod = db.scalar(select(Pod).where(Pod.load_id == load.id))
    return {
        "id": load.id,
        "reference": load.reference,
        "shipper": shipper.name if shipper else None,
        "shipper_user_id": load.shipper_user_id,
        "carrier_org_id": load.carrier_org_id,
        "carrier": carrier.name if carrier else None,
        "origin": load.origin,
        "destination": load.destination,
        "equipment_type": load.equipment_type,
        "commodity": load.commodity,
        "status": load.status,
        "compliance_flag": load.compliance_flag,
        "compliance_reason": load.compliance_reason,
        "rate": {"id": rate.id, "version": rate.version, "base_rate": rate.base_rate, "accessorials": json.loads(rate.accessorials)} if rate else None,
        "pod": {"id": pod.id, "file_name": pod.file_name, "url": pod.url, "verified_at": pod.verified_at.isoformat() if pod.verified_at else None} if pod else None,
        "created_at": load.created_at.isoformat(),
        "updated_at": load.updated_at.isoformat(),
    }


@app.post("/api/v1/loads")
def create_load(payload: LoadIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.create")
    if user.account_type != "broker":
        deny(db, user, "load.create")
    shipper = db.get(User, payload.shipper_user_id)
    if not shipper or shipper.account_type != "shipper":
        raise HTTPException(status_code=400, detail="shipper_user_id must belong to a shipper")
    load = Load(**payload.model_dump(), broker_org_id=user.organization_id, created_by_id=user.id)
    db.add(load)
    db.flush()
    record_status_history(db, load, None, load.status, user, "Load created")
    log_event(db, user, "load.create", "load", None, payload.model_dump())
    db.commit()
    db.refresh(load)
    return serialize_load(db, load)


@app.get("/api/v1/loads/{load_id}")
def get_load(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return serialize_load(db, load_for_user(db, user, load_id))


@app.patch("/api/v1/loads/{load_id}")
def update_load(load_id: int, payload: LoadPatch, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.create")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "load.update", "load", load_id)
    if load.status != "Posted":
        raise HTTPException(status_code=400, detail="Only posted loads can be edited")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(load, field, value)
    load.updated_at = datetime.utcnow()
    log_event(db, user, "load.update", "load", load.id, payload.model_dump(exclude_unset=True))
    db.commit()
    return serialize_load(db, load)


@app.delete("/api/v1/loads/{load_id}", status_code=204)
def delete_load(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> None:
    require_permission(db, user, "load.create")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "load.delete", "load", load_id)
    if load.status != "Posted":
        raise HTTPException(status_code=400, detail="Only posted loads can be deleted")
    log_event(db, user, "load.delete", "load", load.id, {"reference": load.reference})
    db.delete(load)
    db.commit()
    return None


@app.post("/api/v1/loads/{load_id}/assign-carrier")
def assign_carrier(load_id: int, payload: AssignCarrierIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.assign_carrier")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "load.assign_carrier", "load", load_id)
    carrier = db.get(Organization, payload.carrier_org_id)
    if not carrier or carrier.type != "carrier":
        raise HTTPException(status_code=400, detail="carrier_org_id must be a carrier organization")
    if load.status != "Posted":
        raise HTTPException(status_code=400, detail="Only posted loads can be assigned")
    load.carrier_org_id = carrier.id
    previous = load.status
    load.status = "Carrier Assigned"
    apply_compliance(db, load, carrier.id)
    record_status_history(db, load, previous, load.status, user, "Carrier assigned")
    log_event(db, user, "load.assign_carrier", "load", load.id, {"carrier_org_id": carrier.id, "compliance_flag": load.compliance_flag})
    db.commit()
    return serialize_load(db, load)


@app.post("/api/v1/loads/{load_id}/carrier-decision")
def carrier_decision(load_id: int, payload: CarrierDecisionIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.update_status")
    if user.account_type != "carrier":
        deny(db, user, "carrier_decision", "load", load_id)
    load = load_for_user(db, user, load_id)
    if load.status != "Carrier Assigned":
        raise HTTPException(status_code=400, detail="Carrier can accept or decline only while load is Carrier Assigned")
    if payload.decision == "accepted":
        log_event(db, user, "carrier.accept", "load", load.id, {"carrier_org_id": user.organization_id})
        record_status_history(db, load, load.status, load.status, user, "Carrier accepted tender")
    else:
        previous = load.status
        load.carrier_org_id = None
        load.status = "Posted"
        load.compliance_flag = False
        load.compliance_reason = None
        load.updated_at = datetime.utcnow()
        record_status_history(db, load, previous, load.status, user, "Carrier declined tender")
        log_event(db, user, "carrier.decline", "load", load.id, {"carrier_org_id": user.organization_id})
    db.commit()
    return serialize_load(db, load)


@app.post("/api/v1/loads/{load_id}/override-compliance")
def override_compliance(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.override_compliance_flag")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "load.override_compliance_flag", "load", load_id)
    load.compliance_flag = False
    load.compliance_reason = "Overridden by authorized broker user"
    log_event(db, user, "load.override_compliance_flag", "load", load.id)
    db.commit()
    return serialize_load(db, load)


@app.post("/api/v1/loads/{load_id}/status")
def update_status(load_id: int, payload: StatusIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.update_status")
    load = load_for_user(db, user, load_id)
    if user.account_type == "carrier" and payload.status in {"POD Verified", "Invoiced/Closed"}:
        deny(db, user, "broker_only.status", "load", load_id)
    transition(load, payload.status, db, user, "Status updated")
    log_event(db, user, "load.update_status", "load", load.id, {"status": payload.status})
    db.commit()
    return serialize_load(db, load)


@app.post("/api/v1/loads/{load_id}/rate-confirmations")
def confirm_rate(load_id: int, payload: RateIn, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "rate.confirm")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "rate.confirm", "load", load_id)
    if load.status != "Carrier Assigned":
        raise HTTPException(status_code=400, detail="Rate can be confirmed only after carrier assignment")
    if load.compliance_flag:
        raise HTTPException(status_code=409, detail="Compliance flag must be resolved before rate confirmation")
    latest = db.scalar(select(func.max(RateConfirmation.version)).where(RateConfirmation.load_id == load.id)) or 0
    rate = RateConfirmation(
        load_id=load.id,
        carrier_org_id=load.carrier_org_id,
        version=latest + 1,
        base_rate=payload.base_rate,
        accessorials=json.dumps(payload.accessorials),
        confirmed_by_user_id=user.id,
    )
    db.add(rate)
    db.flush()
    load.current_rate_confirmation_id = rate.id
    transition(load, "Rate Confirmed", db, user, "Rate confirmation accepted")
    log_event(db, user, "rate.confirm", "load", load.id, {"version": rate.version, "base_rate": rate.base_rate})
    db.commit()
    return serialize_load(db, load)


@app.get("/api/v1/loads/{load_id}/audit")
def load_audit(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    load_for_user(db, user, load_id)
    events = db.scalars(select(AuditEvent).where(AuditEvent.entity_type == "load", AuditEvent.entity_id == load_id).order_by(AuditEvent.created_at)).all()
    return [{"id": e.id, "action": e.action, "details": json.loads(e.details), "created_at": e.created_at.isoformat(), "user_id": e.user_id} for e in events]


@app.get("/api/v1/loads/{load_id}/history")
def load_history(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    load_for_user(db, user, load_id)
    rows = db.scalars(select(LoadStatusHistory).where(LoadStatusHistory.load_id == load_id).order_by(LoadStatusHistory.created_at)).all()
    return [
        {
            "id": row.id,
            "from_status": row.from_status,
            "to_status": row.to_status,
            "changed_by_user_id": row.changed_by_user_id,
            "note": row.note,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@app.get("/api/v1/rates/{load_id}")
def rate_versions(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    load_for_user(db, user, load_id)
    rates = db.scalars(select(RateConfirmation).where(RateConfirmation.load_id == load_id).order_by(RateConfirmation.version)).all()
    return [{"id": r.id, "version": r.version, "base_rate": r.base_rate, "accessorials": json.loads(r.accessorials), "created_at": r.created_at.isoformat()} for r in rates]


@app.post("/api/v1/pod/{load_id}")
async def upload_pod(
    load_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict[str, Any]:
    require_permission(db, user, "pod.upload")
    load = load_for_user(db, user, load_id)
    if load.status != "Delivered":
        raise HTTPException(status_code=400, detail="POD can be uploaded only after delivery")
    path = UPLOAD_DIR / f"{load_id}-{int(datetime.utcnow().timestamp())}-{file.filename}"
    path.write_bytes(await file.read())
    pod = db.scalar(select(Pod).where(Pod.load_id == load.id))
    if pod:
        pod.file_name = file.filename
        pod.url = str(path.relative_to(BASE_DIR)).replace("\\", "/")
        pod.uploaded_by_user_id = user.id
        pod.uploaded_at = datetime.utcnow()
    else:
        pod = Pod(load_id=load.id, file_name=file.filename, url=str(path.relative_to(BASE_DIR)).replace("\\", "/"), uploaded_by_user_id=user.id)
        db.add(pod)
    log_event(db, user, "pod.upload", "load", load.id, {"file": file.filename})
    db.commit()
    return serialize_load(db, load)


@app.post("/api/v1/pod/{load_id}/verify")
def verify_pod(load_id: int, user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    require_permission(db, user, "load.update_status")
    load = load_for_user(db, user, load_id)
    if user.account_type != "broker":
        deny(db, user, "pod.verify", "load", load_id)
    pod = db.scalar(select(Pod).where(Pod.load_id == load.id))
    if not pod:
        raise HTTPException(status_code=400, detail="No POD uploaded")
    pod.verified_by_user_id = user.id
    pod.verified_at = datetime.utcnow()
    if load.status == "Delivered":
        transition(load, "POD Verified", db, user, "POD verified")
    log_event(db, user, "pod.verify", "load", load.id)
    db.commit()
    return serialize_load(db, load)


@app.get("/api/v1/dashboard")
def dashboard(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    loads = list_loads(user, db)
    flagged = [load for load in loads if load["compliance_flag"]]
    expiring = []
    if user.account_type in {"broker", "carrier"}:
        records = list_compliance(user, db)
        expiring = [r for r in records if date.fromisoformat(r["insurance_expiry"]) <= date.today() + timedelta(days=30)]
    return {
        "account_type": user.account_type,
        "counts": {
            "loads": len(loads),
            "flagged": len(flagged),
            "delivered": len([l for l in loads if l["status"] in {"Delivered", "POD Verified", "Invoiced/Closed"}]),
        },
        "alerts": {
            "compliance_flags": flagged,
            "insurance_expiring": expiring,
        },
        "loads": loads[:10],
    }


@app.get("/api/v1/audit")
def audit(user: Annotated[User, Depends(current_user)], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    if user.account_type == "shipper":
        deny(db, user, "audit.view")
    events = db.scalars(select(AuditEvent).where(AuditEvent.organization_id == user.organization_id).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [{"id": e.id, "action": e.action, "entity_type": e.entity_type, "entity_id": e.entity_id, "details": json.loads(e.details), "created_at": e.created_at.isoformat(), "user_id": e.user_id} for e in events]
