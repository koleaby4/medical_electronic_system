PRAGMA foreign_keys=ON;

-- Patients
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    sex TEXT NOT NULL,
    dob DATE NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- Addresses (1:1 with patients)
CREATE TABLE IF NOT EXISTS addresses (
    patient_id INTEGER PRIMARY KEY,
    line_1 TEXT NOT NULL,
    line_2 TEXT,
    town TEXT NOT NULL,
    postcode TEXT NOT NULL,
    country TEXT NOT NULL,
    FOREIGN KEY(patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Medical check types (catalog)
CREATE TABLE IF NOT EXISTS medical_check_types (
    type_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Medical checks (header)
CREATE TABLE IF NOT EXISTS medical_checks (
    check_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    check_date DATE NOT NULL,
    status TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY(patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY(type_id)
        REFERENCES medical_check_types(type_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id
    ON medical_checks(patient_id);
CREATE INDEX IF NOT EXISTS ix_medical_checks_patient_id_date
    ON medical_checks(patient_id, check_date);

-- Medical check items (detail lines)
CREATE TABLE IF NOT EXISTS medical_check_items (
    check_item_id TEXT PRIMARY KEY,
    check_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    units TEXT,
    value TEXT NOT NULL,
    FOREIGN KEY(check_id)
        REFERENCES medical_checks(check_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_medical_check_items_check_id
    ON medical_check_items(check_id);
CREATE INDEX IF NOT EXISTS ix_medical_check_items_name
    ON medical_check_items(name);

-- Configured input fields for check types
CREATE TABLE IF NOT EXISTS medical_check_type_items (
    type_id INTEGER NOT NULL,
    name TEXT,
    units TEXT,
    input_type TEXT,
    placeholder TEXT,
    FOREIGN KEY(type_id)
        REFERENCES medical_check_types(type_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_mct_type_items_type_id
    ON medical_check_type_items(type_id);
