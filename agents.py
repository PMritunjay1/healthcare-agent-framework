from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from datetime import datetime
from qa_system import QASystem
import database as db
from datetime import datetime

class DataAgent:
    def __init__(self):
        pass

    def get_patient_summary(self, patient_name):
        """Retrieves patient notes from the SQLite database."""
        print(f"Data Agent: Searching database for '{patient_name}'...")
        notes = db.get_notes_by_patient(patient_name)
        if not notes:
            return f"Data Agent: No medical notes found for {patient_name} in the database."
        
        # Format the notes for display, including the DOB
        formatted_notes = [f"- On {date} (Patient DOB: {dob}): {note}" for dob, date, note in notes]
        return f"Found Medical Notes for {patient_name}:\n" + "\n".join(formatted_notes)

    # --- NEW UPDATE METHOD ---
    def update_note(self, patient_name: str, new_note: str) -> str:
        """Updates the most recent note for a patient in the database."""
        print(f"Data Agent: Attempting to update the latest note for '{patient_name}'...")
        success = db.update_latest_medical_note(patient_name, new_note)
        
        if success:
            confirmation = f"Successfully updated the most recent note for {patient_name}."
            return confirmation
        else:
            return f"Error: No existing notes found for {patient_name}. Cannot update."

    # --- NEW DELETE METHOD ---
    def delete_notes(self, patient_name: str) -> str:
        """Deletes all notes for a specific patient."""
        print(f"Data Agent: Attempting to delete all notes for '{patient_name}'...")
        success = db.delete_all_notes_for_patient(patient_name)

        if success:
            confirmation = f"Successfully deleted all medical records for {patient_name}."
            return confirmation
        else:
            return f"Error: No notes found for {patient_name}. Nothing to delete."

# --- UPDATED SCHEDULING AGENT ---
class SchedulingAgent:
    def schedule_appointment(self, patient_name, date_str):
        """Saves a new appointment to the database and returns a confirmation."""
        print(f"Scheduling Agent: Saving appointment for {patient_name} on {date_str} to database...")
        try:
            # We still format the date for the confirmation message
            appointment_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = appointment_date_obj.strftime('%A, %B %d, %Y')
            
            # Save to database
            db.add_appointment(patient_name, date_str)
            
            confirmation = f"CONFIRMED: Appointment for {patient_name} is scheduled for {formatted_date} and has been saved."
            print(f"Scheduling Agent: {confirmation}")
            return confirmation
        except ValueError:
            error_msg = "Error: Invalid date format. Please use YYYY-MM-DD."
            print(f"Scheduling Agent: {error_msg}")
            return error_msg
            
    def get_appointments(self, patient_name: str) -> str:
        """Retrieves all saved appointments for a patient from the database."""
        print(f"Scheduling Agent: Retrieving appointments for '{patient_name}' from database...")
        appointments = db.get_appointments_by_patient(patient_name)
        if not appointments:
            return f"No appointments found for {patient_name}."
        
        # Updated formatting logic to handle potential missing hospital info
        formatted_appts = []
        for date_info, in appointments:
            parts = date_info.split(' at ')
            date_str = parts[0]
            hospital_str = f" at {parts[1]}" if len(parts) > 1 else ""
            formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
            formatted_appts.append(f"- {formatted_date}{hospital_str}")

        return f"Found Appointments for {patient_name}:\n" + "\n".join(formatted_appts)

class WebAgent:
    def __init__(self):
        # ... (init remains the same) ...
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def login_and_enter_note(self, patient_name, dob, note):
        """Saves the note to the database AND automates the mock EMR."""
        try:
            print(f"Web Agent: Saving note for {patient_name} to the database...")
            # Use the updated add_medical_note function
            db.add_medical_note(patient_name, dob, note)
            print("Web Agent: Note saved to database successfully.")

            # ... (the rest of the selenium logic remains the same) ...
            print("Web Agent: Opening mock EMR page...")
            file_path = os.path.abspath('templates/mock_emr.html')
            self.driver.get(f'file:///{file_path}')
            
            wait = WebDriverWait(self.driver, 10)

            print("Web Agent: Logging in...")
            username_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
            username_field.send_keys('doctor')
            self.driver.find_element(By.ID, 'password').send_keys('password')
            self.driver.find_element(By.TAG_NAME, 'button').click()

            print(f"Web Agent: Entering note for {patient_name}...")
            patient_name_field = wait.until(EC.presence_of_element_located((By.ID, 'patient-name')))
            patient_name_field.send_keys(patient_name)

            print(f"Web Agent: Entering DOB {dob}...")
            self.driver.find_element(By.ID, 'dob').send_keys(dob)

            self.driver.find_element(By.ID, 'note').send_keys(note)
            self.driver.find_element(By.XPATH, "//div[@id='data-entry']//button").click()

            status_element = wait.until(EC.presence_of_element_located((By.ID, 'submission-status')))
            status = status_element.text
            
            print(f"Web Agent: Submission status: '{status}'")
            return status
        finally:
            self.driver.quit()

class ClinicalQAAgent:
    def __init__(self):
        # The agent's only job is to initialize our powerful QA System
        self.qa_system = QASystem()

    def answer(self, question: str) -> str:
        """Passes the question to the QA System to get an answer."""
        return self.qa_system.answer_question(question)