import random
from datetime import date, timedelta

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.models.enums import Title, Sex, MedicalCheckType, MedicalCheckStatus
from src.models.patient import Patient
from src.models.medical_check_item import MedicalCheckItem
from faker import Faker

fake = Faker()


def _get_random_patient() -> Patient:
    sex = random.choice(list(Sex))
    match sex:
        case Sex.MALE:
            title = random.choice([Title.MR, Title.DR, Title.LORD, Title.SIR])
            first_name = fake.first_name_male()
            middle_name = fake.first_name_male() if random.random() < 0.5 else None
            last_name = fake.last_name_male()
        case Sex.FEMALE:
            title = random.choice([Title.MRS, Title.MISS, Title.MS])
            first_name = fake.first_name_female()
            middle_name = fake.first_name_female() if random.random() < 0.5 else None
            last_name = fake.last_name_female()
        case _:
            title = random.choice(list(Title))
            first_name = fake.first_name()
            middle_name = fake.middle_name()
            last_name = fake.last_name()

    return Patient(
        title=title,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        sex=sex,
        dob=fake.date_of_birth(minimum_age=16, maximum_age=95),
        email=f"{first_name.lower()}.{last_name.lower()}@gmail.com",
        phone=fake.phone_number(),
    )


def build_sample_patients() -> list[Patient]:
    return [
        Patient(
            title=Title.MR,
            first_name="joHN",
            middle_name="alBert",
            last_name="doE",
            sex=Sex.MALE,
            dob=fake.date_of_birth(minimum_age=16, maximum_age=95),
            email="JOHN.DOE@EXAMPLE.COM",
            phone="+1-555-0100",
        ),
        Patient(
            title=Title.MRS,
            first_name="emily",
            middle_name=None,
            last_name="clark",
            sex=Sex.FEMALE,
            dob=fake.date_of_birth(minimum_age=16, maximum_age=95),
            email="EMILY.CLARK@MAIL.COM",
            phone="+44 20 7946 0001",
        ),
        Patient(
            title=Title.DR,
            first_name="alex",
            middle_name="",
            last_name="taylor",
            sex=Sex.UNKNOWN,
            dob=fake.date_of_birth(minimum_age=45, maximum_age=95),
            email="ALEX.TAYLOR@HEALTH.ORG",
            phone="(555) 0101",
        ),
        Patient(
            title=Title.MX,
            first_name="sam",
            middle_name=None,
            last_name="rivers",
            sex=Sex.SPECIAL,
            dob=fake.date_of_birth(minimum_age=16, maximum_age=35),
            email="SAM.RIVERS@MAIL.NET",
            phone="+1 555 0102",
        ),
        Patient(
            title=Title.MS,
            first_name="olivia",
            middle_name="grace",
            last_name="martin",
            sex=Sex.FEMALE,
            dob=fake.date_of_birth(minimum_age=14, maximum_age=26),
            email="OLIVIA.MARTIN@EXAMPLE.CO.UK",
            phone="555-0103",
        ),
        _get_random_patient(),
        _get_random_patient(),
    ]


def _seed_patients(storage: DbStorage) -> list[Patient]:
    return [storage.patients.create(p) for p in build_sample_patients()]


def _get_random_physicals_items() -> list[MedicalCheckItem]:
    height_cm = random.randint(150, 200)
    height_m = height_cm / 100
    weight = random.randint(45, 150)
    return [
        MedicalCheckItem(name="Height", units="cm", value=str(height_cm)),
        MedicalCheckItem(name="Weight", units="kg", value=str(weight)),
        MedicalCheckItem(name="BMI", units="", value=round(weight / (height_m * height_m), 2)),
        MedicalCheckItem(name="blood pressure (systolic)", units="mmHg", value=str(random.randint(100, 200))),
        MedicalCheckItem(name="blood pressure (diastolic)", units="mmHg", value=str(random.randint(60, 150))),
        MedicalCheckItem(name="Heart Rate", units="bpm", value=str(random.randint(40, 150))),
    ]


def _get_random_blood_items() -> list[MedicalCheckItem]:
    return [
        MedicalCheckItem(name="Hemoglobin", units="g/dL", value="14.0"),
        MedicalCheckItem(name="WBC", units="10^9/L", value="6.5"),
        MedicalCheckItem(name="Platelets", units="10^9/L", value="250"),
        MedicalCheckItem(name="Glucose (fasting)", units="mg/dL", value="92"),
    ]


def _get_check_status(medical_check_items: list[MedicalCheckItem]) -> MedicalCheckStatus:
    if weights := [x for x in medical_check_items if x.name == "Weight"]:
        weight = float(weights[0].value)
        if weight < 40 or weight > 100:
            return MedicalCheckStatus.RED

    if blood_pressures_systolic := [x for x in medical_check_items if x.name == "blood pressure (systolic)"]:
        systolic = float(blood_pressures_systolic[0].value)
        if systolic < 120 or systolic > 180:
            return MedicalCheckStatus.RED

    if blood_pressures_diastolic := [x for x in medical_check_items if x.name == "blood pressure (diastolic)"]:
        diastolic = float(blood_pressures_diastolic[0].value)
        if diastolic < 80 or diastolic > 120:
            return MedicalCheckStatus.RED

    if bmis := [x for x in medical_check_items if x.name == "BMI"]:
        match float(bmis[0].value):
            case x if x < 18.5 or x > 40:
                return MedicalCheckStatus.RED
            case x if x > 30 or x < 40:
                return MedicalCheckStatus.AMBER

    return MedicalCheckStatus.GREEN


def _seed_medical_checks(db: DbStorage, patients: list[Patient]) -> None:
    """Create several dummy medical checks for each patient."""
    today = date.today()
    for p in patients:
        if p.patient_id is None:
            continue

        medical_check_items = _get_random_physicals_items()
        status: MedicalCheckStatus = _get_check_status(medical_check_items)

        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.PHYSICALS.value,
            check_date=today - timedelta(days=random.randint(1, 30)),
            status=status.value,
            medical_check_items=medical_check_items,
            notes="recent physical examination",
        )

        medical_check_items = _get_random_physicals_items()
        status: MedicalCheckStatus = _get_check_status(medical_check_items)

        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.PHYSICALS.value,
            check_date=today - timedelta(days=random.randint(30, 365)),
            status=status.value,
            medical_check_items=_get_random_physicals_items(),
            notes="older physical examination",
        )

        medical_check_items = _get_random_physicals_items()
        status: MedicalCheckStatus = _get_check_status(medical_check_items)

        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.PHYSICALS.value,
            check_date=today - timedelta(days=random.randint(365, 365 * random.randint(1, 5))),
            status=status.value,
            medical_check_items=_get_random_physicals_items(),
            notes="oldest physical examination",
        )

        # Recent blood test
        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.BLOOD.value,
            check_date=today - timedelta(days=random.randint(1, 30)),
            status=random.choice(list(MedicalCheckStatus)).value,
            medical_check_items=_get_random_blood_items(),
            notes="recent blood test",
        )

        # Older blood test
        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.BLOOD.value,
            check_date=today - timedelta(days=random.randint(30, 365)),
            status=random.choice(list(MedicalCheckStatus)).value,
            medical_check_items=_get_random_blood_items(),
            notes="older blood test",
        )

        # Oldest blood test
        db.medical_checks.create(
            patient_id=p.patient_id,
            check_type=MedicalCheckType.BLOOD.value,
            check_date=today - timedelta(days=random.randint(365, 365 * random.randint(1, 5))),
            status=random.choice(list(MedicalCheckStatus)).value,
            medical_check_items=_get_random_blood_items(),
            notes="oldest blood test",
        )


if __name__ == "__main__":
    storage = DbStorage(Settings().duckdb_file)

    if storage.patients.get_all_patients():
        storage.close()
        exit(0)

    try:
        patients = _seed_patients(storage)
        _seed_medical_checks(storage, patients)
    finally:
        storage.close()
