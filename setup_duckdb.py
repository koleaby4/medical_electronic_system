from pathlib import Path

import duckdb

from settings import Settings


def create_tables(db_file: Path):
    with duckdb.connect(db_file) as conn:

        conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_patient_id START 1")

        conn.execute("""
             CREATE TABLE IF NOT EXISTS patients (
                 patient_id INTEGER PRIMARY KEY default nextval('seq_patient_id'),
                 title VARCHAR,
                 first_name VARCHAR,
                 middle_name VARCHAR NULL,
                 last_name VARCHAR,
                 dob DATE,
                 email VARCHAR,
                 phone VARCHAR)
                     """)

if __name__ == "__main__":
    st = Settings()
    create_tables(st.duckdb_file)
