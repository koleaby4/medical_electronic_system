import duckdb
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("INFO")


def create_patients_table(db: str):
    with duckdb.connect(db) as conn:
        conn.execute("CREATE SEQUENCE IF NOT EXISTS patients_id_seq")
        logger.info("Created patients_id_seq (if not exists)")

        conn.execute("""
             CREATE TABLE IF NOT EXISTS patients (
                 patient_id INTEGER PRIMARY KEY DEFAULT nextval('patients_id_seq'),
                 title VARCHAR,
                 first_name VARCHAR,
                 middle_name VARCHAR NULL,
                 last_name VARCHAR,
                 sex VARCHAR,
                 dob DATE,
                 email VARCHAR,
                 phone VARCHAR)
                     """)

        logger.info("Created patients table (if not exists)")


def create_medical_checks_table(db: str):
    with duckdb.connect(db) as conn:
        conn.execute("CREATE SEQUENCE IF NOT EXISTS medical_checks_id_seq")
        logger.info("Created medical_checks_id_seq (if not exists)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medical_checks (
               check_id INTEGER PRIMARY KEY DEFAULT nextval('medical_checks_id_seq'),
               patient_id INTEGER NOT NULL,
               check_type TEXT NOT NULL,
               check_date DATE NOT NULL,
               status TEXT NOT NULL,
               notes TEXT NULL,
               foreign key (patient_id) references patients(patient_id)
            )
            """
        )

        logger.info("Created medical_checks table (if not exists)")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_medical_checks_patient_date
            ON medical_checks(patient_id, check_date);
            """
        )
        logger.info("Ensured idx_medical_checks_patient_date exists")


def medical_check_items_table(db: str):
    with duckdb.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medical_check_items (
                check_item_id UUID PRIMARY KEY DEFAULT uuid(),
                check_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                units TEXT NOT NULL,
                value TEXT NOT NULL,
                foreign key (check_id) references medical_checks(check_id)
            )
            """
        )
        logger.info("Created medical_check_items table (if not exists)")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_medical_check_items_check
            ON medical_check_items(check_id);
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_medical_check_items_name
            ON medical_check_items(name);
            """
        )
        logger.info("Ensured indexes on medical_check_items exist")


def create_tables(db: str):
    create_patients_table(db)
    create_medical_checks_table(db)
    medical_check_items_table(db)


if __name__ == "__main__":
    create_tables("database.duckdb")
