from enum import StrEnum


class AccountType(StrEnum):
    BROKER = "broker"
    CARRIER = "carrier"
    SHIPPER = "shipper"


class AuthorityStatus(StrEnum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    PENDING = "pending"
