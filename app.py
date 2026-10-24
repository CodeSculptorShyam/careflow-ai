import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "appointments.db"

st.set_page_config(page_title="CareFlow AI", page_icon="🩺", layout="wide")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                appointment_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
            )
        """)

def get_appointments():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM appointments ORDER BY appointment_date, appointment_time"
        ).fetchall()

def add_appointment(name, appt_date, appt_time, appt_type):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO appointments
            (patient_name, appointment_date, appointment_time, appointment_type, status, created_at)
            VALUES (?, ?, ?, ?, 'Scheduled', ?)
        """, (name.strip(), appt_date.isoformat(), appt_time.strftime("%H:%M"),
              appt_type, datetime.now().isoformat(timespec="seconds")))

def update_status(appointment_id, status):
    with get_connection() as conn:
        conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))

def get_followups():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM followups ORDER BY due_date").fetchall()

def add_followup(title, due_date, priority):
    with get_connection() as conn:
        conn.execute("INSERT INTO followups (title, due_date, priority) VALUES (?, ?, ?)",
                     (title.strip(), due_date.isoformat(), priority))

def update_followup_status(task_id, status):
    with get_connection() as conn:
        conn.execute("UPDATE followups SET status = ? WHERE id = ?", (status, task_id))

def generate_reminder(appt, style):
    """Use Gemini if configured; otherwise provide a clearly labelled local template."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    prompt = (
        "Write a short, polite healthcare administrative appointment reminder. "
        "Do not provide medical advice, diagnosis, or treatment suggestions. "
        "Do not include a patient's name or sensitive details. "
        f"Appointment date: {appt['appointment_date']}. "
        f"Appointment time: {appt['appointment_time']}. "
        f"Appointment type: {appt['appointment_type']}. "
        f"Message style: {style}. "
        "Include a brief instruction to contact the clinic if the appointment needs changing."
    )
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            if response.text:
                return response.text.strip(), "Generated with Gemini AI"
        except Exception as exc:
            return (
                f"Hello, this is a reminder of your {appt['appointment_type']} appointment "
                f"on {appt['appointment_date']} at {appt['appointment_time']}. "
                "Please contact the clinic if you need to make a change.\n\n"
                f"AI service was unavailable ({type(exc).__name__}); a fallback template is shown.",
                "Fallback template (AI request failed)"
            )
    return (
        f"Hello, this is a reminder of your {appt['appointment_type']} appointment "
        f"on {appt['appointment_date']} at {appt['appointment_time']}. "
        "Please contact the clinic if you need to make a change.",
        "Template mode — add GEMINI_API_KEY to enable AI generation"
    )

init_db()

st.title("🩺 CareFlow AI")
st.caption("A small healthcare administration prototype for appointments, follow-ups, and AI-assisted reminders.")
st.info("Demo only: use fictional data. This tool does not provide medical advice and should not be used to store real patient information.")

appointments = get_appointments()
followups = get_followups()
today = date.today().isoformat()
upcoming = [a for a in appointments if a["appointment_date"] >= today and a["status"] != "Cancelled"]
pending_followups = [f for f in followups if f["status"] == "Pending"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total appointments", len(appointments))
m2.metric("Upcoming", len(upcoming))
m3.metric("Pending follow-ups", len(pending_followups))
m4.metric("Completed", sum(1 for a in appointments if a["status"] == "Completed"))

tab1, tab2, tab3 = st.tabs(["Appointments", "AI reminder generator", "Follow-up tasks"])

with tab1:
    left, right = st.columns([1, 1.5])
    with left:
        st.subheader("Add an appointment")
        with st.form("appointment_form", clear_on_submit=True):
            patient_name = st.text_input("Patient name (use fictional demo names)")
            appt_date = st.date_input("Appointment date", value=date.today())
            appt_time = st.time_input("Appointment time")
            appt_type = st.selectbox("Appointment type", ["General consultation", "Dental check-up", "Follow-up visit", "Vaccination", "Health screening", "Other"])
            submitted = st.form_submit_button("Save appointment", type="primary")
            if submitted:
                if not patient_name.strip():
                    st.error("Please enter a demo patient name.")
                elif appt_date < date.today():
                    st.error("Please choose today or a future date.")
                else:
                    add_appointment(patient_name, appt_date, appt_time, appt_type)
                    st.success("Appointment saved.")
                    st.rerun()
    with right:
        st.subheader("Appointment list")
        rows = get_appointments()
        if not rows:
            st.write("No appointments yet. Add one using the form.")
        for appt in rows:
            with st.container(border=True):
                col_a, col_b = st.columns([2, 1])
                col_a.markdown(f"**{appt['patient_name']}** · {appt['appointment_type']}")
                col_a.caption(f"{appt['appointment_date']} at {appt['appointment_time']} · ID {appt['id']}")
                options = ["Scheduled", "Completed", "Cancelled"]
                current_index = options.index(appt["status"]) if appt["status"] in options else 0
                new_status = col_b.selectbox("Status", options, index=current_index, key=f"status_{appt['id']}", label_visibility="collapsed")
                if new_status != appt["status"]:
                    update_status(appt["id"], new_status)
                    st.rerun()

with tab2:
    st.subheader("Create an appointment reminder")
    rows = get_appointments()
    if not rows:
        st.warning("Add an appointment first.")
    else:
        labels = {f"#{a['id']} — {a['patient_name']} · {a['appointment_date']} {a['appointment_time']}": a for a in rows}
        selected_label = st.selectbox("Choose an appointment", list(labels.keys()))
        style = st.selectbox("Tone", ["Warm and friendly", "Professional and concise", "Simple English"])
        if st.button("Generate reminder", type="primary"):
            message, source = generate_reminder(labels[selected_label], style)
            st.session_state["last_reminder"] = message
            st.session_state["last_reminder_source"] = source
        if "last_reminder" in st.session_state:
            st.text_area("Reminder message", st.session_state["last_reminder"], height=150)
            st.caption(st.session_state.get("last_reminder_source", ""))
            st.download_button("Download reminder as text", st.session_state["last_reminder"], file_name="appointment_reminder.txt", mime="text/plain")

with tab3:
    left, right = st.columns([1, 1.5])
    with left:
        st.subheader("Add a follow-up task")
        with st.form("followup_form", clear_on_submit=True):
            task_title = st.text_input("Task title", placeholder="e.g., Confirm appointment time")
            due_date = st.date_input("Due date", value=date.today(), key="followup_due")
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            add_task = st.form_submit_button("Add task", type="primary")
            if add_task:
                if not task_title.strip():
                    st.error("Please enter a task title.")
                else:
                    add_followup(task_title, due_date, priority)
                    st.success("Task added.")
                    st.rerun()
    with right:
        st.subheader("Follow-up queue")
        tasks = get_followups()
        if not tasks:
            st.write("No tasks yet.")
        for task in tasks:
            with st.container(border=True):
                a, b = st.columns([2, 1])
                a.markdown(f"**{task['title']}**")
                a.caption(f"Due {task['due_date']} · Priority: {task['priority']}")
                task_status = b.selectbox("Task status", ["Pending", "Done"], index=0 if task["status"] == "Pending" else 1, key=f"task_{task['id']}", label_visibility="collapsed")
                if task_status != task["status"]:
                    update_followup_status(task["id"], task_status)
                    st.rerun()

st.divider()
st.caption("Prototype note: Gemini integration is optional. Without an API key, the app uses a labelled local reminder template.")
