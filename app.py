# app.py (Upgraded with Conversational State Management)

import streamlit as st
from orchestrator import Orchestrator

# --- Page Configuration ---
st.set_page_config(
    page_title="Healthcare Automation Framework",
    page_icon="🤖",
    layout="wide"
)

# --- Sidebar ---
with st.sidebar:
    st.title("About the Framework")
    st.markdown("""
    This is an AI-powered multi-agent system designed to automate administrative healthcare tasks. 
    You can interact with it using natural language commands.
    """)

    st.subheader("Available Agent Skills")
    st.info("""
    - **Get Patient Records:** Retrieves medical notes from the database.
    - **Update Patient Records:** Updates the most recent note for a patient.
    - **Delete Patient Records:** Removes all notes for a patient.
    - **Enter New Note:** Adds a new patient note via a simulated EMR.
    - **Schedule Appointment:** Books a new appointment through conversation.
    - **Get Appointments:** Retrieves a patient's existing appointments.
    - **Clinical Q&A:** Answers general medical questions.
    """)

    st.subheader("Example Commands")
    st.code("summary for Sarah Tancredi")
    st.code("update note for Sarah Tancredi: Patient has fully recovered.")
    st.code("delete notes for Sarah Tancredi")
    st.code("schedule an appointment") # Starts a conversation
    st.code("get appointments for Michael Chen")
    st.code("enter note: New Patient, 2001-07-25, Patient has a sore throat.")
    st.code("What are the symptoms of hypertension?")


# --- App Title (Main Area) ---
st.title("Healthcare Automation Framework 🩺")
st.caption("An AI-powered multi-agent system to automate administrative tasks.")


# --- Initialize the Orchestrator and Chat History ---
# Using @st.cache_resource to ensure the Orchestrator is created only once
@st.cache_resource
def get_orchestrator():
    print("Initializing Orchestrator for the first time...")
    return Orchestrator()

orchestrator = get_orchestrator()


if "messages" not in st.session_state:
    # Add a welcome message to start
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I assist you today?"}
    ]

# --- NEW: Initialize conversation state ---
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {}


# --- Display existing messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- Handle User Input ---
if prompt := st.chat_input("Enter your command..."):
    # Add user message to the chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("The AI agent is thinking..."):
            # Pass the current conversation state to the orchestrator
            response = orchestrator.run(prompt, st.session_state.conversation_state)
            
            # --- CONVERSATIONAL STATE LOGIC ---
            if response.startswith("I can help with that."):
                # The agent is asking a question, so we are in a conversation.
                st.session_state.conversation_state["active_agent"] = "Scheduler"
                st.session_state.conversation_state["last_question"] = response
                # Initialize details if this is the start of the conversation
                if "details" not in st.session_state.conversation_state:
                    st.session_state.conversation_state["details"] = {}

            elif response.startswith("✅ **CONFIRMED:**"):
                # The scheduling conversation is finished, so we clear the state.
                st.session_state.conversation_state = {}
            
            elif "Error:" in response or "Could not parse" in response or "not sure how to handle" in response:
                # If there's an error, clear the conversation state to avoid getting stuck
                st.session_state.conversation_state = {}
            
            st.markdown(response)
    
    # Add the assistant's response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": response})