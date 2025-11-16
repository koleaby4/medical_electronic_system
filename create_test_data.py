from datetime import date, timedelta

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.models.enums import Title, Sex, MedicalCheckType, MedicalCheckStatus
from src.models.patient import Patient
from src.models.medical_check import MedicalCheckItem


def build_sample_patients() -> list[Patient]:
    return [
        Patient(
            title=Title.MR,
            first_name="joHN",
            middle_name="alBert",
            last_name="doE",
            sex=Sex.MALE,
            dob=date(1990, 1, 2),
            email="JOHN.DOE@EXAMPLE.COM",
            phone="+1-555-0100",
        ),
        Patient(
            title=Title.MRS,
            first_name="emily",
            middle_name=None,
            last_name="clark",
            sex=Sex.FEMALE,
            dob=date(1985, 12, 30),
            email="EMILY.CLARK@MAIL.COM",
            phone="+44 20 7946 0001",
        ),
        Patient(
            title=Title.DR,
            first_name="alex",
            middle_name="",
            last_name="taylor",
            sex=Sex.UNKNOWN,
            dob=date(1978, 7, 14),
            email="ALEX.TAYLOR@HEALTH.ORG",
            phone="(555) 0101",
        ),
        Patient(
            title=Title.MX,
            first_name="sam",
            middle_name=None,
            last_name="rivers",
            sex=Sex.SPECIAL,
            dob=date(2001, 6, 9),
            email="SAM.RIVERS@MAIL.NET",
            phone="+1 555 0102",
        ),
        Patient(
            title=Title.MS,
            first_name="olivia",
            middle_name="grace",
            last_name="martin",
            sex=Sex.FEMALE,
            dob=date(1995, 3, 22),
            email="OLIVIA.MARTIN@EXAMPLE.CO.UK",
            phone="555-0103",
        ),
    ]


def seed_patients(storage: DbStorage) -> list[Patient]:
    """Insert sample patients into DB and return them with assigned IDs."""
    created: list[Patient] = []
    for p in build_sample_patients():
        created.append(storage.patients.create(p))
    return created


def build_physicals_items() -> list[MedicalCheckItem]:
    return [
        MedicalCheckItem(name="Height", units="cm", value="180"),
        MedicalCheckItem(name="Weight", units="kg", value="75"),
        MedicalCheckItem(name="BMI", units="", value="23.1"),
        MedicalCheckItem(name="Blood Pressure", units="mmHg", value="120/80"),
        MedicalCheckItem(name="Heart Rate", units="bpm", value="72"),
    ]


def build_blood_items() -> list[MedicalCheckItem]:
    return [
        MedicalCheckItem(name="Hemoglobin", units="g/dL", value="14.0"),
        MedicalCheckItem(name="WBC", units="10^9/L", value="6.5"),
        MedicalCheckItem(name="Platelets", units="10^9/L", value="250"),
        MedicalCheckItem(name="Glucose (fasting)", units="mg/dL", value="92"),
    ]


def seed_medical_checks(storage: DbStorage, patients: list[Patient]) -> None:
    """Create several dummy medical checks for each patient."""
    today = date.today()
    for p in patients:
        if p.patient_id is None:
            continue

        # Recent physicals check
        storage.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.PHYSICALS.value,
            check_date=today - timedelta(days=7),
            status=MedicalCheckStatus.AMBER.value,
            medical_check_items=build_physicals_items(),
            notes="Routine annual physical examination.",
        )

        # Older blood test
        storage.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.BLOOD.value,
            check_date=today - timedelta(days=40),
            status=MedicalCheckStatus.GREEN.value,
            medical_check_items=build_blood_items(),
            notes="Standard CBC and fasting glucose.",
        )


def main() -> None:
    db_path = Settings().duckdb_file
    storage = DbStorage(db_path)

    # If there is already data, do nothing to avoid duplicates
    if storage.patients.get_all_patients():
        storage.close()
        return

    try:
        patients = seed_patients(storage)
        seed_medical_checks(storage, patients)
    finally:
        storage.close()


if __name__ == "__main__":
    main()
