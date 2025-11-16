import duckdb
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("INFO")


def create_tables(db: str):
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


def create_test_results_table(db: str):
    with duckdb.connect(db) as conn:
        conn.execute("CREATE SEQUENCE IF NOT EXISTS medical_checks_id_seq")
        logger.info("Created medical_checks_id_seq (if not exists)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS medical_checks (
                check_id INTEGER PRIMARY KEY DEFAULT nextval('medical_checks_id_seq'),
                patient_id INTEGER NOT NULL,
                check_type TEXT NOT NULL,
                check_date DATE NOT NULL,
                results JSON NOT NULL,
                foreign key (patient_id) references patients(patient_id)
            )""")

        logger.info("Created medical_checks table (if not exists)")


if __name__ == "__main__":
    create_tables("database.duckdb")
