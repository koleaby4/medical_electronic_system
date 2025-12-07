import logging
import random
import re
from contextlib import suppress
from datetime import date, timedelta

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.models.enums import Title, Sex, MedicalCheckType, MedicalCheckStatus
from src.models.patient import Patient
from src.models.address import Address
from src.models.medical_check_item import MedicalCheckItem
from src.models.medical_check_template import MedicalCheckTemplateItem
from faker import Faker

fake = Faker()
logger = logging.getLogger(__name__)


def _get_random_patient() -> Patient:
    def _get_random_address() -> Address:
        return Address(
            line_1=fake.street_address(),
            line_2=None,
            town=fake.city(),
            postcode=fake.postcode(),
            country="United Kingdom",
        )

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
            middle_name = fake.first_name()
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
        address=_get_random_address(),
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
            address=Address(
                line_1="1 Baker Street",
                line_2=None,
                town="London",
                postcode="SW1A1AA",
                country="United Kingdom",
            ),
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
            address=Address(
                line_1="221B Baker Street",
                line_2="",
                town="London",
                postcode="EC1A1BB",
                country="United Kingdom",
            ),
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
            address=Address(
                line_1="10 Downing Street",
                line_2=None,
                town="London",
                postcode="W1A0AX",
                country="United Kingdom",
            ),
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
            address=Address(
                line_1="1600 Pennsylvania Ave",
                line_2=None,
                town="Washington",
                postcode="SW1A2AA",
                country="United Kingdom",
            ),
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
            address=Address(
                line_1="742 Evergreen Terrace",
                line_2=None,
                town="Springfield",
                postcode="SW1A1AA",
                country="United Kingdom",
            ),
        ),
        _get_random_patient(),
        _get_random_patient(),
    ]


def _seed_patients(storage: DbStorage) -> list[Patient]:
    return [storage.patients.save(p) for p in build_sample_patients()]


def _extract_example_number(placeholder: str) -> float | None:
    if not placeholder:
        return None
    if m := re.search(r"(-?\d+(?:[\.,]\d+)?)", placeholder):
        with suppress(Exception):
            return float(m.group(1).replace(",", "."))
    return None


def _generate_value_for_item(name: str, input_type: str, placeholder: str) -> str:
    ex = _extract_example_number(placeholder)
    if input_type == "number" and ex is not None:
        val = random.uniform(ex * 0.8, ex * 1.2)  # sample within ±20% of example
        if "." in str(ex):
            return f"{val:.1f}"
        return str(int(round(val)))

    if input_type != "number":
        return ""

    values = {
        "height": str(random.randint(150, 200)),
        "weight": f"{random.uniform(50, 110):.1f}",
        "systolic": str(random.randint(100, 180)),
        "diastolic": str(random.randint(60, 120)),
        "heart rate": str(random.randint(50, 110)),
        "pulse": str(random.randint(50, 110)),
        "hemoglobin": f"{random.uniform(12.0, 17.5):.1f}",
        "white blood": f"{random.uniform(3.5, 11.0):.1f}",
        "wbc": f"{random.uniform(3.5, 11.0):.1f}",
        "platelet": str(int(random.uniform(150, 450))),
        "glucose": f"{random.uniform(3.9, 6.5):.1f}",
        "cholesterol": f"{random.uniform(3.0, 6.5):.1f}",
    }

    param = name.strip().lower()

    return values.get(param, f"{random.uniform(0, 100):.1f}")


def _build_items_from_template(storage: DbStorage, template_name: str) -> list[MedicalCheckItem] | None:
    try:
        templates = storage.medical_check_templates.list_medical_check_templates()
        match_t = next(
            (t for t in templates if (t.template_name or "").strip().lower() == template_name.strip().lower()),
            None,
        )
        if not match_t or match_t.template_id is None:
            return None

        full = storage.medical_check_templates.get_template(template_id=match_t.template_id)
        if not full:
            return None

        items: list[MedicalCheckItem] = []
        for ti in full.items:
            value = _generate_value_for_item(ti.name, (ti.input_type or "short_text").lower(), ti.placeholder)
            items.append(MedicalCheckItem(name=ti.name, units=ti.units, value=str(value)))
        return items
    except Exception:
        return None


def _get_random_physicals_items(storage: DbStorage) -> list[MedicalCheckItem]:
    templated = _build_items_from_template(storage, "physicals")
    if templated is not None and len(templated) > 0:
        return templated

    height_cm = random.randint(150, 200)
    weight = random.randint(45, 150)
    return [
        MedicalCheckItem(name="height", units="cm", value=str(height_cm)),
        MedicalCheckItem(name="weight", units="kg", value=str(weight)),
        MedicalCheckItem(name="blood pressure (systolic)", units="mmHg", value=str(random.randint(100, 200))),
        MedicalCheckItem(name="blood pressure (diastolic)", units="mmHg", value=str(random.randint(60, 150))),
    ]


def _get_random_blood_items(storage: DbStorage) -> list[MedicalCheckItem]:
    templated = _build_items_from_template(storage, "blood")
    if templated is not None and len(templated) > 0:
        return templated

    # Todo: delete?
    # Fallback (legacy)
    return [
        MedicalCheckItem(name="Hemoglobin", units="g/dL", value="14.2"),
        MedicalCheckItem(name="White Blood Cell Count (WBC)", units="×10^9/L", value="6.5"),
        MedicalCheckItem(name="Platelet Count", units="×10^9/L", value="250"),
        MedicalCheckItem(name="Blood Glucose (fasting)", units="mmol/L", value="5.2"),
        MedicalCheckItem(name="Total Cholesterol", units="mmol/L", value="4.8"),
    ]


def _get_check_status(medical_check_items: list[MedicalCheckItem]) -> MedicalCheckStatus:
    if weights := [x for x in medical_check_items if x.name == "weight"]:
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
    today = date.today()
    for p in [p for p in patients if p.patient_id]:
        for i in range(random.randint(5, 12)):
            check_type = random.choice([MedicalCheckType.PHYSICALS, MedicalCheckType.BLOOD])
            check_date = today - timedelta(days=random.randint(1, 365 * random.randint(1, 5)))

            match check_type:
                case MedicalCheckType.PHYSICALS:
                    medical_check_items = _get_random_physicals_items(db)

                case MedicalCheckType.BLOOD:
                    medical_check_items = _get_random_blood_items(db)

                case _:
                    raise ValueError(f"Invalid medical {check_type=}")

            status: MedicalCheckStatus = _get_check_status(medical_check_items)
            db.medical_checks.save(
                patient_id=p.patient_id,
                check_type=check_type.value,
                check_date=check_date,
                status=status.value,
                medical_check_items=medical_check_items,
                notes=f"{check_type=} examination on {check_date=}",
            )


def _seed_medical_check_templates(storage: DbStorage) -> None:
    """Ensure a 'physicals' template with 4 standard items exists.

    Idempotent: uses upsert with existing template_id if a template with the
    same name is found (case-insensitive).
    """
    # Find existing template by name (case-insensitive)
    existing = None
    try:
        templates = storage.medical_check_templates.list_medical_check_templates()
        existing = next((t for t in templates if (t.template_name or "").strip().lower() == "physicals"), None)
    except Exception:
        existing = None

    template_id = existing.template_id if existing and getattr(existing, "template_id", None) is not None else None

    items = [
        MedicalCheckTemplateItem(name="height", units="cm", input_type="number", placeholder="e.g. 180"),
        MedicalCheckTemplateItem(name="weight", units="kg", input_type="number", placeholder="e.g. 75.5"),
        MedicalCheckTemplateItem(
            name="blood pressure (systolic)", units="mmHg", input_type="number", placeholder="e.g. 120"
        ),
        MedicalCheckTemplateItem(
            name="blood pressure (diastolic)", units="mmHg", input_type="number", placeholder="e.g. 80"
        ),
    ]

    new_id = storage.medical_check_templates.upsert(
        template_id=template_id,
        template_name="physicals",
        items=items,
    )
    logger.info("Seeded/updated medical_check_template 'physicals' with id=%s", new_id)


def _seed_medical_check_template_blood(storage: DbStorage) -> None:
    """Ensure a 'blood' template exists with standard blood test items.

    Idempotent: finds an existing template named 'blood' (case-insensitive) and
    upserts items accordingly.
    """
    existing = None
    try:
        templates = storage.medical_check_templates.list_medical_check_templates()
        existing = next((t for t in templates if (t.template_name or "").strip().lower() == "blood"), None)
    except Exception:
        existing = None

    template_id = existing.template_id if existing and getattr(existing, "template_id", None) is not None else None

    items = [
        MedicalCheckTemplateItem(name="Hemoglobin", units="g/dL", input_type="number", placeholder="e.g. 14.2"),
        MedicalCheckTemplateItem(
            name="White Blood Cell Count (WBC)", units="×10^9/L", input_type="number", placeholder="e.g. 6.5"
        ),
        MedicalCheckTemplateItem(
            name="Platelet Count", units="×10^9/L", input_type="number", placeholder="e.g. 250"
        ),
        MedicalCheckTemplateItem(
            name="Blood Glucose (fasting)", units="mmol/L", input_type="number", placeholder="e.g. 5.2"
        ),
        MedicalCheckTemplateItem(
            name="Total Cholesterol", units="mmol/L", input_type="number", placeholder="e.g. 4.8"
        ),
    ]

    new_id = storage.medical_check_templates.upsert(
        template_id=template_id,
        template_name="blood",
        items=items,
    )
    logger.info("Seeded/updated medical_check_template 'blood' with id=%s", new_id)


if __name__ == "__main__":
    storage = DbStorage(Settings().db_file)

    # Always ensure templates exist, regardless of patient data presence
    _seed_medical_check_templates(storage)
    _seed_medical_check_template_blood(storage)

    if storage.patients.get_all_patients():
        logger.warning("Database already contains data. Skipping seeding.")
        storage.close()
        exit(0)

    logger.warning("Creating test data...")

    try:
        patients = _seed_patients(storage)
        _seed_medical_checks(storage, patients)
    finally:
        storage.close()
