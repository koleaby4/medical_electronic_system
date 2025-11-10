import duckdb

from settings import Settings


def create_tables(db: str):
    with duckdb.connect(db) as conn:
        conn.execute("CREATE SEQUENCE IF NOT EXISTS patients_id_seq")

        conn.execute("""
             CREATE TABLE IF NOT EXISTS patients (
                 patient_id INTEGER PRIMARY KEY DEFAULT nextval('patients_id_seq'),
                 title VARCHAR,
                 first_name VARCHAR,
                 middle_name VARCHAR NULL,
                 last_name VARCHAR,
                 dob DATE,
                 email VARCHAR,
                 phone VARCHAR)
                     """)


if __name__ == "__main__":
    db_file = Settings().duckdb_file
    create_tables(str(db_file))
