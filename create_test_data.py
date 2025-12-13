import logging
import random
import re
from contextlib import suppress
from datetime import date, timedelta

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.models.address import Address
from src.models.enums import MedicalCheckStatus, Sex, Title
from src.models.medical_check_item import MedicalCheckItem
from src.models.medical_check_type import MedicalCheckTypeItem
from src.models.patient import Patient

logger = logging.getLogger(__name__)


def _get_random_patient() -> Patient:
    # Deprecated: left in place to avoid import errors; no longer used by seeding.
    def _get_random_address() -> Address:
        return Address(
            line_1="100 Random Road",
            line_2=None,
            town="Nowhere",
            postcode="ZZ1 1ZZ",
            country="United Kingdom",
        )

    return Patient(
        title=Title.MR,
        first_name="Random",
        middle_name=None,
        last_name="Person",
        sex=Sex.UNKNOWN,
        dob=date(1980, 1, 1),
        email="random.person@example.com",
        phone="00000",
        address=_get_random_address(),
    )


def build_sample_patients() -> list[Patient]:
    # Deterministic, realistic demo patients (fixed DOBs/contacts)
    return [
        Patient(
            title=Title.MR,
            first_name="joHN",
            middle_name="alBert",
            last_name="doE",
            sex=Sex.MALE,
            dob=date(1985, 5, 17),
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
            dob=date(1990, 9, 12),
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
            dob=date(1960, 2, 3),
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
            dob=date(2001, 7, 22),
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
            dob=date(2008, 11, 5),
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
        Patient(
            title=Title.SIR,
            first_name="arthur",
            middle_name="",
            last_name="kent",
            sex=Sex.MALE,
            dob=date(1948, 3, 9),
            email="ARTHUR.KENT@EXAMPLE.ORG",
            phone="555-0104",
            address=Address(
                line_1="5 Fleet Street",
                line_2=None,
                town="London",
                postcode="WC2N5DU",
                country="United Kingdom",
            ),
        ),
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


def _build_items_for_check_type(db: DbStorage, check_name: str) -> list[MedicalCheckItem] | None:
    try:
        medical_check_types = db.medical_check_types.list_medical_check_types()
        match_t = next((t for t in medical_check_types if t.name == check_name), None)
        if not match_t:
            return None

        full = db.medical_check_types.get_check_type(type_id=match_t.type_id)
        if not full:
            return None

        items: list[MedicalCheckItem] = []
        for ti in full.items:
            value = _generate_value_for_item(ti.name, (ti.input_type or "short_text").lower(), ti.placeholder)
            items.append(MedicalCheckItem(name=ti.name, units=ti.units, value=str(value)))
        return items
    except Exception:
        return None


def _physicals_items(height_cm: int, weight_kg: float, systolic: int, diastolic: int) -> list[MedicalCheckItem]:
    return [
        MedicalCheckItem(name="height", units="cm", value=str(height_cm)),
        MedicalCheckItem(name="weight", units="kg", value=f"{weight_kg:.1f}"),
        MedicalCheckItem(name="blood pressure (systolic)", units="mmHg", value=str(systolic)),
        MedicalCheckItem(name="blood pressure (diastolic)", units="mmHg", value=str(diastolic)),
    ]


def _blood_items(*, hb: float, wbc: float, plt: int, glu: float, chol: float) -> list[MedicalCheckItem]:
    return [
        MedicalCheckItem(name="Hemoglobin", units="g/dL", value=f"{hb:.1f}"),
        MedicalCheckItem(name="White Blood Cell Count (WBC)", units="×10^9/L", value=f"{wbc:.1f}"),
        MedicalCheckItem(name="Platelet Count", units="×10^9/L", value=str(int(plt))),
        MedicalCheckItem(name="Blood Glucose (fasting)", units="mmol/L", value=f"{glu:.1f}"),
        MedicalCheckItem(name="Total Cholesterol", units="mmol/L", value=f"{chol:.1f}"),
    ]


def _get_check_status(medical_check_items: list[MedicalCheckItem]) -> MedicalCheckStatus:
    # Determine an overall status based on item values; worst item wins.
    def worse(a: MedicalCheckStatus, b: MedicalCheckStatus) -> MedicalCheckStatus:
        order = {MedicalCheckStatus.GREEN: 0, MedicalCheckStatus.AMBER: 1, MedicalCheckStatus.RED: 2}
        return a if order[a] >= order[b] else b

    overall = MedicalCheckStatus.GREEN

    # Weight evaluation
    if weights := [x for x in medical_check_items if x.name.lower() == "weight"]:
        w = float(weights[0].value)
        status = (
            MedicalCheckStatus.RED
            if w < 40 or w > 120
            else MedicalCheckStatus.AMBER
            if w < 50 or w > 100
            else MedicalCheckStatus.GREEN
        )
        overall = worse(overall, status)

    # Blood pressure evaluation
    sys_item = next((x for x in medical_check_items if x.name.lower() == "blood pressure (systolic)"), None)
    dia_item = next((x for x in medical_check_items if x.name.lower() == "blood pressure (diastolic)"), None)
    if sys_item and dia_item:
        s = float(sys_item.value)
        d = float(dia_item.value)
        # Green: ~ 100-139/60-89, Amber: 140-179/90-119, Red: <90 or >=180 systolic; <60 or >=120 diastolic
        if s < 90 or s >= 180 or d < 60 or d >= 120:
            overall = worse(overall, MedicalCheckStatus.RED)
        elif (140 <= s < 180) or (90 <= d < 120) or (s < 100) or (d < 60):
            overall = worse(overall, MedicalCheckStatus.AMBER)
        else:
            overall = worse(overall, MedicalCheckStatus.GREEN)

    # BMI if explicitly provided
    if bmis := [x for x in medical_check_items if x.name.upper() == "BMI"]:
        bmi = float(bmis[0].value)
        status = (
            MedicalCheckStatus.RED
            if bmi < 18.5 or bmi >= 40
            else MedicalCheckStatus.AMBER
            if bmi >= 30
            else MedicalCheckStatus.GREEN
        )
        overall = worse(overall, status)

    # Blood metrics
    name_map = {x.name.lower(): x for x in medical_check_items}
    # Hemoglobin (generic range)
    if hb := name_map.get("hemoglobin"):
        v = float(hb.value)
        status = MedicalCheckStatus.GREEN
        if v < 11.0 or v > 18.5:
            status = MedicalCheckStatus.RED
        elif v < 12.0 or v > 17.5:
            status = MedicalCheckStatus.AMBER
        overall = worse(overall, status)

    if wbc := name_map.get("white blood cell count (wbc)"):
        v = float(wbc.value)
        status = MedicalCheckStatus.GREEN
        if v < 2.0 or v > 20.0:
            status = MedicalCheckStatus.RED
        elif v < 3.5 or v > 11.0:
            status = MedicalCheckStatus.AMBER
        overall = worse(overall, status)

    if plt := name_map.get("platelet count"):
        v = float(plt.value)
        status = MedicalCheckStatus.GREEN
        if v < 100 or v > 600:
            status = MedicalCheckStatus.RED
        elif v < 150 or v > 450:
            status = MedicalCheckStatus.AMBER
        overall = worse(overall, status)

    if glu := name_map.get("blood glucose (fasting)"):
        v = float(glu.value)
        status = MedicalCheckStatus.GREEN
        if v >= 7.0 or v < 3.0:
            status = MedicalCheckStatus.RED
        elif 5.6 <= v < 7.0 or 3.0 <= v < 3.9:
            status = MedicalCheckStatus.AMBER
        overall = worse(overall, status)

    if chol := name_map.get("total cholesterol"):
        v = float(chol.value)
        status = MedicalCheckStatus.GREEN
        if v > 6.5:
            status = MedicalCheckStatus.RED
        elif v >= 5.0:
            status = MedicalCheckStatus.AMBER
        overall = worse(overall, status)

    return overall


def _seed_medical_checks(db: DbStorage, patients: list[Patient]) -> None:
    today = date.today()

    def add_check(patient_id: int, check_type: str, offset_days: int, items: list[MedicalCheckItem], notes: str):
        status = _get_check_status(items)
        db.medical_checks.save(
            patient_id=patient_id,
            check_type=check_type,
            check_date=today - timedelta(days=offset_days),
            status=status.value,
            medical_check_items=items,
            notes=notes,
        )

    for idx, p in enumerate(patients):
        # Diversify trajectories by patient index to avoid everyone ending in Red.
        # Grouping (deterministic by idx):
        # 0: Stable, ends Green; 1: Stable, ends Amber;
        # 2: Improving, ends Green; 3: Improving, ends Amber;
        # 4: Worsening, ends Amber; 5: Worsening, ends Red.

        group = idx % 6

        if group == 0:
            # Stable Green: keep within normal ranges with small variations.
            add_check(
                p.patient_id,
                "physicals",
                90,
                _physicals_items(175, 48.0, 118, 78),
                "Physicals - underweight but BP normal (Amber)",
            )
            add_check(
                p.patient_id,
                "physicals",
                60,
                _physicals_items(175, 70.0, 116, 76),
                "Routine physicals - normal (Green)",
            )
            add_check(p.patient_id, "physicals", 30, _physicals_items(175, 71.0, 120, 78), "Physicals - normal (Green)")
            add_check(
                p.patient_id, "physicals", 10, _physicals_items(175, 72.0, 124, 80), "Physicals - stable normal (Green)"
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=13.6, wbc=6.0, plt=240, glu=5.5, chol=5.1),
                "Blood - borderline lipids (Amber)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=14.0, wbc=6.3, plt=250, glu=5.1, chol=4.6),
                "Blood - normal (Green)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=14.1, wbc=6.4, plt=255, glu=4.9, chol=4.7),
                "Blood - stable normal (Green)",
            )

        elif group == 1:
            # Stable Amber: avoid any Red; mild hypertension persists.
            add_check(
                p.patient_id,
                "physicals",
                90,
                _physicals_items(175, 50.0, 118, 78),
                "Physicals - low-normal weight (Green)",
            )
            add_check(
                p.patient_id,
                "physicals",
                60,
                _physicals_items(175, 72.0, 135, 86),
                "Physicals - high-normal BP (Green)",
            )
            add_check(
                p.patient_id, "physicals", 30, _physicals_items(175, 70.0, 142, 91), "Physicals - elevated BP (Amber)"
            )
            add_check(
                p.patient_id,
                "physicals",
                10,
                _physicals_items(175, 71.0, 150, 95),
                "Physicals - persistent hypertension (Amber)",
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=13.9, wbc=6.1, plt=230, glu=5.6, chol=5.3),
                "Blood - borderline (Amber)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=14.2, wbc=6.6, plt=255, glu=5.2, chol=4.7),
                "Blood - normal (Green)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=14.0, wbc=6.4, plt=250, glu=5.8, chol=5.4),
                "Blood - mild dyslipidemia (Amber)",
            )

        elif group == 2:
            # Improving to Green: early Red -> later Green.
            add_check(
                p.patient_id,
                "physicals",
                90,
                _physicals_items(175, 125.0, 170, 110),
                "Physicals - obesity & stage-2 HTN (Red)",
            )
            add_check(
                p.patient_id,
                "physicals",
                60,
                _physicals_items(175, 105.0, 145, 95),
                "Physicals - improving BP/weight (Amber)",
            )
            add_check(
                p.patient_id,
                "physicals",
                30,
                _physicals_items(175, 95.0, 136, 88),
                "Physicals - near-normal BP (Green)",
            )
            add_check(
                p.patient_id, "physicals", 10, _physicals_items(175, 90.0, 124, 80), "Physicals - controlled (Green)"
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=10.8, wbc=12.2, plt=120, glu=7.2, chol=6.7),
                "Blood - multiple abnormalities (Red)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=12.2, wbc=11.5, plt=160, glu=5.9, chol=5.3),
                "Blood - improving (Amber)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=13.8, wbc=6.8, plt=220, glu=5.1, chol=4.6),
                "Blood - normalized (Green)",
            )

        elif group == 3:
            # Improving to Amber: early Red -> later Amber (no Red at latest).
            add_check(
                p.patient_id,
                "physicals",
                90,
                _physicals_items(175, 122.0, 182, 121),
                "Physicals - hypertensive crisis (Red)",
            )
            add_check(
                p.patient_id,
                "physicals",
                60,
                _physicals_items(175, 110.0, 160, 100),
                "Physicals - improving but high (Amber)",
            )
            add_check(
                p.patient_id, "physicals", 30, _physicals_items(175, 100.0, 142, 92), "Physicals - stage-1 HTN (Amber)"
            )
            add_check(
                p.patient_id,
                "physicals",
                10,
                _physicals_items(175, 98.0, 145, 95),
                "Physicals - persistent stage-1 HTN (Amber)",
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=10.9, wbc=12.0, plt=130, glu=7.1, chol=6.6),
                "Blood - severe abnormalities (Red)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=12.1, wbc=11.3, plt=155, glu=5.9, chol=5.4),
                "Blood - improving (Amber)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=12.4, wbc=10.8, plt=170, glu=5.7, chol=5.2),
                "Blood - stable borderline (Amber)",
            )

        elif group == 4:
            # Worsening to Amber: start Green, end Amber (avoid Red latest).
            add_check(p.patient_id, "physicals", 90, _physicals_items(175, 72.0, 120, 78), "Physicals - normal (Green)")
            add_check(
                p.patient_id, "physicals", 60, _physicals_items(175, 80.0, 130, 86), "Physicals - high-normal (Green)"
            )
            add_check(
                p.patient_id, "physicals", 30, _physicals_items(175, 92.0, 140, 90), "Physicals - elevated BP (Amber)"
            )
            add_check(
                p.patient_id,
                "physicals",
                10,
                _physicals_items(175, 95.0, 150, 96),
                "Physicals - worsening hypertension (Amber)",
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=13.8, wbc=6.0, plt=230, glu=5.0, chol=4.6),
                "Blood - normal (Green)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=13.7, wbc=7.5, plt=225, glu=5.5, chol=4.9),
                "Blood - borderline (Green)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=13.5, wbc=11.5, plt=160, glu=5.8, chol=5.4),
                "Blood - trending worse (Amber)",
            )

        else:  # group == 5
            # Worsening to Red: start Green, end Red.
            add_check(p.patient_id, "physicals", 90, _physicals_items(175, 70.0, 118, 78), "Physicals - normal (Green)")
            add_check(
                p.patient_id, "physicals", 60, _physicals_items(175, 85.0, 136, 88), "Physicals - high-normal (Green)"
            )
            add_check(
                p.patient_id, "physicals", 30, _physicals_items(175, 96.0, 152, 96), "Physicals - stage-1 HTN (Amber)"
            )
            add_check(
                p.patient_id,
                "physicals",
                10,
                _physicals_items(175, 102.0, 182, 121),
                "Physicals - hypertensive crisis (Red)",
            )

            add_check(
                p.patient_id,
                "blood",
                75,
                _blood_items(hb=14.0, wbc=6.4, plt=250, glu=5.1, chol=4.7),
                "Blood - normal (Green)",
            )
            add_check(
                p.patient_id,
                "blood",
                45,
                _blood_items(hb=13.2, wbc=7.8, plt=220, glu=5.6, chol=5.1),
                "Blood - borderline (Amber)",
            )
            add_check(
                p.patient_id,
                "blood",
                5,
                _blood_items(hb=10.5, wbc=12.5, plt=120, glu=7.4, chol=6.8),
                "Blood - abnormalities detected (Red)",
            )


def _seed_medical_check_templates(storage: DbStorage) -> None:
    items = [
        MedicalCheckTypeItem(name="height", units="cm", input_type="number", placeholder="e.g. 180"),
        MedicalCheckTypeItem(name="weight", units="kg", input_type="number", placeholder="e.g. 75.5"),
        MedicalCheckTypeItem(
            name="blood pressure (systolic)", units="mmHg", input_type="number", placeholder="e.g. 120"
        ),
        MedicalCheckTypeItem(
            name="blood pressure (diastolic)", units="mmHg", input_type="number", placeholder="e.g. 80"
        ),
    ]

    new_id = storage.medical_check_types.upsert(
        template_id=None,
        check_name="physicals",
        items=items,
    )
    logger.info("Seeded/updated medical_check_template 'physicals' with id=%s", new_id)


def _seed_medical_check_template_blood(storage: DbStorage) -> None:
    items = [
        MedicalCheckTypeItem(name="Hemoglobin", units="g/dL", input_type="number", placeholder="e.g. 14.2"),
        MedicalCheckTypeItem(
            name="White Blood Cell Count (WBC)", units="×10^9/L", input_type="number", placeholder="e.g. 6.5"
        ),
        MedicalCheckTypeItem(name="Platelet Count", units="×10^9/L", input_type="number", placeholder="e.g. 250"),
        MedicalCheckTypeItem(
            name="Blood Glucose (fasting)", units="mmol/L", input_type="number", placeholder="e.g. 5.2"
        ),
        MedicalCheckTypeItem(name="Total Cholesterol", units="mmol/L", input_type="number", placeholder="e.g. 4.8"),
    ]

    new_id = storage.medical_check_types.upsert(
        template_id=None,
        check_name="blood",
        items=items,
    )
    logger.info("Seeded/updated medical_check_template 'blood' with id=%s", new_id)


if __name__ == "__main__":
    storage = DbStorage(Settings().db_file)

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
