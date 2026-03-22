# orchestrator.py (Updated for OpenAI API Deployment)

import re
from datetime import datetime

# --- IMPORTS HAVE BEEN CHANGED ---
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI  # Use the OpenAI LLM

from langchain_core.output_parsers import StrOutputParser
from agents import DataAgent, WebAgent, SchedulingAgent, ClinicalQAAgent
from langchain_core.prompts import PromptTemplate
import database as db
import streamlit as st

# --- NEW: LOAD THE API KEY FROM THE .env FILE ---
load_dotenv()

# --- Caching Functions (no changes here) ---
@st.cache_resource
def get_data_agent():
    print("Initializing DataAgent (Singleton)...")
    return DataAgent()

@st.cache_resource
def get_scheduling_agent():
    print("Initializing SchedulingAgent (Singleton)...")
    return SchedulingAgent()

@st.cache_resource
def get_clinical_qa_agent():
    print("Initializing ClinicalQAAgent (Singleton)...")
    return ClinicalQAAgent()

# --- The Main Orchestrator Class ---
class Orchestrator:
    def __init__(self):
        db.init_db()
        
        # --- THE MAIN CHANGE IS HERE ---
        # We are switching to the fast and powerful OpenAI API.
        # It will automatically find your API key from the loaded .env file.
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
        print("Orchestrator: Connected to OpenAI API (gpt-4o-mini).")
        # --- END OF MAIN CHANGE ---
        
        self.data_agent = get_data_agent()
        self.scheduling_agent = get_scheduling_agent()
        # --- TEMPORARILY DISABLE THE QA AGENT ---
        self.clinical_qa_agent = get_clinical_qa_agent()

        prompt_template = """
        You are a helpful assistant who decides which tool to use.
        - 'Data Agent - Get': For retrieving patient notes.
        - 'Data Agent - Update': For UPDATING a note.
        - 'Data Agent - Delete': For DELETING notes.
        - 'Web Agent': For entering a NEW note.
        - 'Scheduling Agent - Add': For scheduling a NEW appointment. THIS CAN BE A CONVERSATION.
        - 'Scheduling Agent - Get': For retrieving EXISTING appointments.
        - 'Clinical QA Agent': For answering general medical questions.

        User Request: "{query}"
        Respond with only the tool name.
        """
        self.prompt = PromptTemplate(template=prompt_template, input_variables=["query"])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _parse_scheduling_query(self, query: str) -> dict:
        # ... (This method does not need to change) ...
        details = {}
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', query)
        if date_match:
            details['date'] = date_match.group(1)
        
        hospital_match = re.search(r'\b(at|in)\s+([\w\s]+Hospital|[\w\s]+Clinic)\b', query, re.IGNORECASE)
        if hospital_match:
            details['hospital'] = hospital_match.group(2).strip()
            
        return details

    def run(self, user_query, conversation_state: dict = None):
        # ... (This entire method does not need to change) ...
        # --- Conversation Handling ---
        if conversation_state and conversation_state.get("active_agent") == "Scheduler":
            details = conversation_state.get("details", {})
            last_question = conversation_state.get("last_question", "")
            
            if "patient name" in last_question:
                details["patient_name"] = user_query
            elif "date" in last_question:
                details["date"] = user_query
            elif "hospital" in last_question:
                details["hospital"] = user_query
            
            return self.scheduling_agent.process_booking_request(details)

        # --- New Task Handling ---
        print("\nOrchestrator: Thinking...")
        chosen_tool = self.chain.invoke({"query": user_query}).strip()
        print(f"Orchestrator's Action: The LLM chose to use the '{chosen_tool}'.")

        # --- CORRECT AND COMPLETE LOGIC FOR ALL AGENTS ---
        if "Scheduling Agent - Add" in chosen_tool:
            initial_details = self._parse_scheduling_query(user_query)
            return self.scheduling_agent.process_booking_request(initial_details)

        elif "Data Agent - Get" in chosen_tool:
            patient_name = user_query.split("for ")[-1].replace('?', '')
            return self.data_agent.get_patient_summary(patient_name)
        
        elif "Data Agent - Update" in chosen_tool:
            try:
                name_part = user_query.split(' for ')[1]
                patient_name = name_part.split(':')[0].strip()
                new_note = name_part.split(':', 1)[1].strip()
                return self.data_agent.update_note(patient_name, new_note)
            except Exception as e:
                return "Could not parse update request. Please use format: 'update note for [Name]: [New Note]'"

        elif "Data Agent - Delete" in chosen_tool:
            try:
                patient_name = user_query.split(' for ')[1].strip()
                return self.data_agent.delete_notes(patient_name)
            except Exception as e:
                return "Could not parse delete request. Please use format: 'delete notes for [Patient Name]'"

        elif "Web Agent" in chosen_tool:
            web_agent = WebAgent()
            try:
                content = user_query.split(':', 1)[1].strip()
                parts = content.split(',')
                if len(parts) < 3:
                    return "Invalid format. Please provide Name, DOB, and a Note, separated by commas."
                patient_name = parts[0].strip()
                dob = parts[1].strip()
                note = ",".join(parts[2:]).strip()
                return web_agent.login_and_enter_note(patient_name, dob, note)
            except Exception as e:
                return "Could not parse Web Agent query. Please use format: 'enter note: [Name], [YYYY-MM-DD], [Note]'"
        
        elif "Scheduling Agent - Get" in chosen_tool:
            try:
                patient_name = user_query.split(' for ')[1].strip()
                return self.scheduling_agent.get_appointments(patient_name)
            except Exception as e:
                return "Could not parse request. Please use format: 'get appointments for [Patient Name]'"

        elif "Clinical QA Agent" in chosen_tool:
            return self.clinical_qa_agent.answer(user_query)

        else:
            return f"I'm not sure how to handle that. The LLM suggested '{chosen_tool}'. Please rephrase your query."