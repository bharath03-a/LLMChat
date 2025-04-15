import streamlit as st
import os
import pandas as pd
from datetime import datetime
import random
import re

# Set page configuration
st.set_page_config(page_title="Medical Notes Processor", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .section-header {
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .note-container {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
        background-color: white;
    }
    .file-list {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 10px;
    }
    .filter-box {
        margin-bottom: 10px;
    }
    .folder-path {
        background-color: #f9f9f9;
        padding: 5px;
        border: 1px solid #ddd;
        border-radius: 3px;
        margin-bottom: 5px;
        font-family: monospace;
    }
    .task-btn {
        background-color: #f0f0f0;
        padding: 8px 12px;
        border-radius: 5px;
        border: 1px solid #ddd;
        text-align: center;
        margin: 5px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Function to generate sample medical notes
def generate_sample_notes(num_notes=10):
    notes = []
    
    chief_complaints = [
        "persistent cough and shortness of breath",
        "chest pain and dizziness",
        "fever and chills",
        "lower back pain",
        "headache and blurred vision",
        "abdominal pain and nausea",
        "joint pain and stiffness",
        "sore throat and difficulty swallowing",
        "skin rash and itching",
        "fatigue and weakness"
    ]
    
    physicians = [
        "Dr. Jane Smith", 
        "Dr. John Watson", 
        "Dr. Emily Chen", 
        "Dr. Michael Rodriguez", 
        "Dr. Sarah Johnson"
    ]
    
    # Create sample patients
    for i in range(1, num_notes+1):
        patient_id = f"MRN_{random.randint(100000, 999999)}"
        date = datetime.now().replace(
            day=random.randint(1, 28),
            month=random.randint(1, 12)
        ).strftime("%m/%d/%Y")
        
        age = random.randint(25, 85)
        gender = random.choice(["male", "female"])
        name = f"Patient_{i}"
        complaint = random.choice(chief_complaints)
        physician = random.choice(physicians)
        
        duration = random.randint(1, 4)
        duration_unit = random.choice(["day", "week", "month"])
        if duration > 1:
            duration_unit += "s"
        
        # Create past medical history
        conditions = []
        if random.random() > 0.7:
            conditions.append("Hypertension")
        if random.random() > 0.8:
            conditions.append("Diabetes Type 2")
        if random.random() > 0.7:
            conditions.append("Seasonal allergies")
        if random.random() > 0.9:
            conditions.append("Asthma")
        
        notes.append({
            "id": f"{i}",
            "filename": f"MRN_Date_NoteID_EncType_{i}",
            "patient_id": patient_id,
            "date": date,
            "physician": physician,
            "chief_complaint": complaint,
            "patient_info": f"{name} is a {age}-year-old {gender} who reports a {complaint} for the past {duration} {duration_unit}.",
            "past_medical_history": conditions
        })
    
    return notes

# Main app
def main():
    # Initialize session state for folders and notes
    if 'project_folder' not in st.session_state:
        st.session_state.project_folder = "C:\\Users\\Me\\Documents\\test_project"
    if 'output_folder' not in st.session_state:
        st.session_state.output_folder = "C:\\Users\\Me\\Documents\\test_project\\out1"
    if 'cohort_config' not in st.session_state:
        st.session_state.cohort_config = ""
    if 'notes' not in st.session_state:
        st.session_state.notes = generate_sample_notes(123)
    if 'selected_note' not in st.session_state:
        st.session_state.selected_note = None
    if 'filter_text' not in st.session_state:
        st.session_state.filter_text = ""
    
    # Main layout - 3 columns
    col1, col2, col3 = st.columns([1, 1, 2])
    
    # Column 1 - Folder selection and filtering
    with col1:
        st.markdown('<div class="main-header">Medical Notes Processor</div>', unsafe_allow_html=True)

        # Project folder selection
        st.markdown('<div class="section-header">Project folder</div>', unsafe_allow_html=True)
        project_folder_input = st.text_input("", 
                                           st.session_state.project_folder, 
                                           key="project_folder_input", 
                                           label_visibility="collapsed")
        if project_folder_input != st.session_state.project_folder:
            st.session_state.project_folder = project_folder_input
        
        # Output folder selection
        st.markdown('<div class="section-header">Output folder</div>', unsafe_allow_html=True)
        output_folder_input = st.text_input("", 
                                          st.session_state.output_folder, 
                                          key="output_folder_input", 
                                          label_visibility="collapsed")
        if output_folder_input != st.session_state.output_folder:
            st.session_state.output_folder = output_folder_input
        
        # Cohort config
        st.markdown('<div class="section-header">Cohort config</div>', unsafe_allow_html=True)
        cohort_config_input = st.text_input("", 
                                          "Total: 123 patients, 456 notes", 
                                          key="cohort_config_input", 
                                          label_visibility="collapsed",
                                          disabled=True)
        
        # Filter list
        st.markdown('<div class="section-header">Filter list by</div>', unsafe_allow_html=True)
        filter_text = st.text_input("", st.session_state.filter_text, key="filter_input", 
                                 placeholder="file substring", 
                                 label_visibility="collapsed")
        if filter_text != st.session_state.filter_text:
            st.session_state.filter_text = filter_text
        
        # File list
        st.markdown('<div class="section-header">Files</div>', unsafe_allow_html=True)
        
        filtered_notes = st.session_state.notes
        if st.session_state.filter_text:
            filtered_notes = [note for note in st.session_state.notes 
                           if st.session_state.filter_text.lower() in note['filename'].lower()]
        
        # Display list of files
        for i, note in enumerate(filtered_notes[:20]):  # Show only first 20 for performance
            if st.button(f"{i+1}. {note['filename']}", key=f"note_{i}", use_container_width=True):
                st.session_state.selected_note = note
        
        if len(filtered_notes) > 20:
            st.write("...")
    
    # Column 2 - Tasks and options
    with col2:
        st.markdown('<div class="main-header">Primary tasks</div>', unsafe_allow_html=True)
        
        task_buttons = ["Concept rules", "Process notes", "Review outputs"]
        for task in task_buttons:
            if st.button(task, use_container_width=True):
                st.toast(f"{task} selected")
        
        st.markdown('<div class="main-header">Advanced settings</div>', unsafe_allow_html=True)
        
        advanced_buttons = ["Sentence rules", "Section rules", "Negation rules"]
        for setting in advanced_buttons:
            if st.button(setting, use_container_width=True):
                st.toast(f"{setting} selected")
    
    # Column 3 - Note display
    with col3:
        if st.session_state.selected_note:
            note = st.session_state.selected_note
            
            with st.container():
                st.markdown('<div class="note-container">', unsafe_allow_html=True)
                
                st.markdown(f"**Date of Visit:** {note['date']}")
                st.markdown(f"**Primary Care Physician:** {note['physician']}")
                
                st.markdown("**Chief Complaint:**")
                st.markdown(f"Patient presents with a complaint of {note['chief_complaint']} for the past two weeks.")
                
                st.markdown("**History of Present Illness:**")
                st.markdown(note['patient_info'])
                st.markdown(f"The {note['chief_complaint'].split(' ')[0]} is worse at night and has been accompanied by shortness of breath, especially during physical exertion. He denies any fever, chills, or chest pain. He has tried over-the-counter cough suppressants with minimal relief.")
                
                st.markdown("**Past Medical History:**")
                for condition in note['past_medical_history']:
                    st.markdown(f"• {condition}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                col_prev, col_next = st.columns([1, 1])
                with col_next:
                    if st.button("Next attachment"):
                        st.toast("Moving to next attachment")
        else:
            st.info("Select a note from the list to view details")

if __name__ == "__main__":
    main()