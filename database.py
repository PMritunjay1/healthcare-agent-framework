import sqlite3
import os

DB_FILE = "healthcare.db"
NOTES_FILE = "data/medical_notes.txt"

def init_db():
    """Initializes the database, creates tables with proper schema."""
    db_exists = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create medical_notes table with a dedicated DOB column
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medical_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        dob TEXT,
        date TEXT,
        note TEXT NOT NULL
    )
    """)

    # Create appointments table (no change here)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        appointment_date TEXT NOT NULL
    )
    """)

    # One-time data migration from .txt file
    if not db_exists and os.path.exists(NOTES_FILE):
        print("First time setup: Migrating data to new schema...")
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        records = content.split('\n---\n')
        for record in records:
            if record.strip():
                try:
                    lines = record.strip().split('\n')
                    patient_name = lines[0].replace('Patient: ', '').strip()
                    date = lines[1].replace('Date: ', '').strip()
                    note = lines[2].replace('Note: ', '').strip()
                    # Add a placeholder for DOB for migrated records
                    cursor.execute("INSERT INTO medical_notes (patient_name, dob, date, note) VALUES (?, ?, ?, ?)",
                                   (patient_name, 'UNKNOWN', date, note))
                except IndexError:
                    print(f"Skipping malformed record in .txt file: {record}")
        print("Data migration successful!")

    conn.commit()
    conn.close()

# --- Updated Functions ---

def get_notes_by_patient(patient_name: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Now we also select the DOB
    cursor.execute("SELECT dob, date, note FROM medical_notes WHERE patient_name LIKE ?", ('%' + patient_name + '%',))
    notes = cursor.fetchall()
    conn.close()
    return notes

def add_medical_note(patient_name: str, dob: str, note: str):
    """Adds a new medical note with a DOB to the database."""
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO medical_notes (patient_name, dob, date, note) VALUES (?, ?, ?, ?)",
                   (patient_name, dob, current_date, note))
    conn.commit()
    conn.close()

def update_latest_medical_note(patient_name: str, new_note_text: str) -> bool:
    """Finds the most recent note for a patient and updates ONLY the note content."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM medical_notes WHERE patient_name LIKE ? ORDER BY date DESC, id DESC LIMIT 1", ('%' + patient_name + '%',))
    result = cursor.fetchone()
    if result:
        note_id = result[0]
        cursor.execute("UPDATE medical_notes SET note = ? WHERE id = ?", (new_note_text, note_id))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False

def add_appointment(patient_name: str, appointment_date: str):
    # ... (this function remains the same) ...
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_name, appointment_date) VALUES (?, ?)",
                   (patient_name, appointment_date))
    conn.commit()
    conn.close()

def get_appointments_by_patient(patient_name: str) -> list:
    # ... (this function remains the same) ...
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT appointment_date FROM appointments WHERE patient_name LIKE ?", ('%' + patient_name + '%',))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def delete_all_notes_for_patient(patient_name: str) -> bool:
    """Deletes all medical notes for a given patient."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medical_notes WHERE patient_name LIKE ?", ('%' + patient_name + '%',))
    # The changes attribute tells us if any rows were actually deleted
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0