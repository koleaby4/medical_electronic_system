from enum import StrEnum, Enum


class Title(StrEnum):
    MR = "Mr"
    MRS = "Mrs"
    MS = "Ms"
    MISS = "Miss"
    MX = "Mx"
    DR = "Dr"
    SIR = "Sir"
    DAME = "Dame"
    LORD = "Lord"
    LADY = "Lady"


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    SPECIAL = "special"


class MedicalCheckStatus(StrEnum):
    RED = "Red"
    AMBER = "Amber"
    GREEN = "Green"


class AllergySeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life-threatening"


class AllergyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"


class AllergyCategory(str, Enum):
    DRUG = "drug"
    FOOD = "food"
    ENVIRONMENT = "environment"
    OTHER = "other"
