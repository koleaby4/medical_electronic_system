from enum import StrEnum


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


class MedicalCheckType(StrEnum):
    PHYSICALS = "physicals"
    BLOOD = "blood"
    COLONOSCOPY = "colonoscopy"
