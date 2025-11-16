from datetime import date

from settings import Settings
from src.data_access.db_storage import DbStorage
from src.models.enums import Title, Sex
from src.models.patient import Patient


def main() -> None:
    db_path = Settings().duckdb_file
    storage = DbStorage(db_path)

    if storage.patients.get_all_patients():
        return

    try:
        samples: list[Patient] = [
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
        for p in samples:
            storage.patients.create(p)
    finally:
        storage.close()


if __name__ == "__main__":
    main()
