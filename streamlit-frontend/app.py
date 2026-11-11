import csv

import os

import requests

import streamlit as st

import pandas as pd

import plotly.express as px

# =====================================================

# PAGE CONFIGURATION

# =====================================================

st.set_page_config(

    page_title="Patient Health Records",

    page_icon="🏥",

    layout="wide"

)

API_URL = "http://localhost:8080/api/patient"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

DIAGNOSIS_MAPPING_PATH = r"C:\PatientHealthRecords\dataset\diagnosis_mapping_final.csv"

MAPPING_PATHS = [

    r"C:\PatientHealthRecords\dataset\IDS_mapping.csv",

    os.path.join(DATA_PATH, "IDS_mapping.csv")

]

# =====================================================

# CUSTOM CSS

# =====================================================

st.markdown("""

<style>

.main {

    background-color: #f5f8fc;

}

.header {

    padding: 22px;

    background: linear-gradient(90deg, #123456, #2874A6);

    color: white;

    border-radius: 12px;

    margin-bottom: 25px;

}

.header h1 {

    color: white;

    font-size: 30px;

}

.header p {

    color: white;

    font-size: 15px;

}

div[data-testid="stMetric"] {

    background-color: white;

    padding: 16px;

    border-radius: 10px;

    border: 1px solid #e5e7eb;

}

</style>

""", unsafe_allow_html=True)

# =====================================================

# HEADER

# =====================================================

st.markdown("""
<div class="header">
    <h1>🏥 Patient Health Records Management System</h1>
    <p>Centralized Patient Information and Medical History Dashboard</p>
</div>
""", unsafe_allow_html=True)

# =====================================================

# SIDEBAR

# =====================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(

    "Select Section",

    ["Dashboard", "Patient Search"]

)

st.sidebar.markdown("---")

st.sidebar.info(

    "Database: Apache HBase\n\n"

    "Backend: Java HTTP Server\n\n"

    "Frontend: Streamlit"

)

# =====================================================

# DATASET LOADING

# =====================================================

@st.cache_data

def load_datasets():

    patients = pd.read_csv(os.path.join(DATA_PATH, "patients.csv"))

    admissions = pd.read_csv(os.path.join(DATA_PATH, "admissions.csv"))

    diagnoses = pd.read_csv(os.path.join(DATA_PATH, "diagnoses.csv"))

    medications = pd.read_csv(os.path.join(DATA_PATH, "medications.csv"))

    return patients, admissions, diagnoses, medications

@st.cache_data

def load_id_mappings():

    """

    Reads the lookup sections in IDS_mapping.csv.

    The file is optional; the app continues to work without it.

    """

    mapping_file = next(

        (path for path in MAPPING_PATHS if os.path.exists(path)),

        None

    )

    if mapping_file is None:

        return {}

    mappings = {}

    current_section = None

    try:

        with open(mapping_file, "r", encoding="utf-8-sig", newline="") as file:

            reader = csv.reader(file)

            for row in reader:

                if not row:

                    current_section = None

                    continue

                first = row[0].strip()

                second = row[1].strip() if len(row) > 1 else ""

                if first.endswith("_id") and second.lower() == "description":

                    current_section = first

                    mappings[current_section] = {}

                    continue

                if current_section and first and second:

                    mappings[current_section][first] = second

    except (OSError, UnicodeError, csv.Error):

        return {}

    return mappings

# =====================================================

# DIAGNOSIS DESCRIPTION LOOKUP

@st.cache_data

def load_diagnosis_mappings():

    """

    Loads exact CMS code descriptions and verified category-level descriptions

    from diagnosis_mapping_final.csv.

    """

    if not os.path.exists(DIAGNOSIS_MAPPING_PATH):

        return {}

    try:

        df = pd.read_csv(DIAGNOSIS_MAPPING_PATH, dtype=str).fillna("")

        result = {}

        for _, row in df.iterrows():

            code = str(row.get("normalized_code", "")).strip().upper()

            if not code:

                continue

            result[code] = {

                "description": str(row.get("description", "")).strip(),

                "mapping_type": str(row.get("mapping_type", "")).strip()

            }

        return result

    except (OSError, UnicodeError, pd.errors.ParserError):

        return {}

def diagnosis_code_details(value, mappings):

    code = str(value).strip().upper()

    if code in ("", "NAN", "?", "NONE"):

        return "Not recorded", "Not available"

    normalized = code.replace(".", "")

    mapping = mappings.get(normalized)

    if mapping:

        description = mapping.get("description", "")

        mapping_type = mapping.get("mapping_type", "")

        if mapping_type == "Exact" and description:

            return description, "Exact CMS match"

        if mapping_type == "Category" and description:

            return description, "Verified category-level description"

    return "Description unavailable in the current ICD-9-CM reference", "Unmapped code"

MEDICATION_LABELS = {

    "metformin": "Metformin", "repaglinide": "Repaglinide", "nateglinide": "Nateglinide",

    "chlorpropamide": "Chlorpropamide", "glimepiride": "Glimepiride", "glipizide": "Glipizide",

    "glyburide": "Glyburide", "pioglitazone": "Pioglitazone", "rosiglitazone": "Rosiglitazone",

    "acarbose": "Acarbose", "miglitol": "Miglitol", "tolazamide": "Tolazamide",

    "insulin": "Insulin", "glyburide-metformin": "Glyburide / Metformin",

    "glipizide-metformin": "Glipizide / Metformin", "glimepiride-pioglitazone": "Glimepiride / Pioglitazone",

    "metformin-rosiglitazone": "Metformin / Rosiglitazone", "metformin-pioglitazone": "Metformin / Pioglitazone",

    "change": "Medication Regimen Changed", "diabetesMed": "Diabetes Medication Prescribed"

}

def medication_label(key):

    return MEDICATION_LABELS.get(key, key.replace("-", " ").replace("_", " ").title())

def medication_value(key, value):

    text = readable_value(key, value, {})

    if key == "change":

        return {"Ch": "Medication regimen changed", "No": "No medication change"}.get(text, text)

    if key == "diabetesMed":

        return {"Yes": "Prescribed", "No": "Not prescribed"}.get(text, text)

    return {"Steady": "Dosage unchanged", "Up": "Dosage increased", "Down": "Dosage decreased", "No": "Not prescribed"}.get(text, text)

# API FUNCTION

# =====================================================

def fetch_patient(patient_id):

    try:

        response = requests.get(

            API_URL,

            params={"patientId": patient_id},

            timeout=120

        )

        if response.status_code == 200:

            return response.json(), None

        if response.status_code == 404:

            return None, "Patient not found."

        if response.status_code == 400:

            return None, "Invalid patient ID."

        return None, f"API Error: HTTP {response.status_code}"

    except requests.exceptions.ConnectionError:

        return None, (

            "Cannot connect to Java backend. "

            "Please start the Java HTTP server."

        )

    except requests.exceptions.Timeout:

        return None, (

            "The backend request timed out. "

            "Check that HBase and the Java backend are running."

        )

    except requests.exceptions.RequestException as error:

        return None, str(error)

    except ValueError:

        return None, "The backend returned an invalid response."

# =====================================================

# DISPLAY NAME MAPPINGS

# =====================================================

ADMISSION_LABELS = {

    "A1Cresult": "HbA1c Test Result",

    "admission_source_id": "How the Patient Was Referred",

    "admission_type_id": "Type of Hospital Admission",

    "discharge_disposition_id": "Discharge Destination",

    "num_lab_procedures": "Number of Laboratory Tests",

    "num_medications": "Number of Medications",

    "num_procedures": "Number of Medical Procedures",

    "number_emergency": "Previous Emergency Visits",

    "number_inpatient": "Previous Inpatient Visits",

    "number_outpatient": "Previous Outpatient Visits",

    "patient_nbr": "Patient ID",

    "payer_code": "Insurance / Payer Code",

    "readmitted": "Hospital Readmission Status",

    "time_in_hospital": "Length of Hospital Stay (Days)",

    "max_glu_serum": "Maximum Blood Glucose Test Result",

    "medical_specialty": "Medical Specialty"

}

DIAGNOSIS_LABELS = {

    "diag_1": "Primary Diagnosis Code",

    "diag_2": "Secondary Diagnosis Code",

    "diag_3": "Additional Diagnosis Code",

    "number_diagnoses": "Number of Diagnoses Recorded"

}

def readable_value(key, value, id_mappings):

    if value is None:

        return "Not recorded"

    value_text = str(value).strip()

    if value_text in ("", "nan", "NaN", "?"):

        return "Not recorded"

    if key in (

        "admission_type_id",

        "discharge_disposition_id",

        "admission_source_id"

    ):

        description = id_mappings.get(key, {}).get(value_text)

        if description:

            return f"{description} (Code: {value_text})"

    if key == "readmitted":

        return {

            "NO": "Not readmitted",

            ">30": "Readmitted after 30 days",

            "<30": "Readmitted within 30 days"

        }.get(value_text, value_text)

    if key == "medical_specialty":

        return value_text.replace("-", " ").replace("_", " ").title()

    return value_text

# =====================================================

# PATIENT DISPLAY

# =====================================================

def display_patient(patient, id_mappings, diagnosis_mappings):

    demographics = patient.get("demographics", {})

    encounters = patient.get("encounters", [])

    st.success("Patient records retrieved successfully!")

    st.markdown("## 👤 Patient Profile")

    col1, col2, col3 = st.columns(3)

    col1.metric("Patient ID", patient.get("patient_id", "N/A"))

    col2.metric("Age Group", demographics.get("age", "Not recorded"))

    col3.metric("Gender", demographics.get("gender", "Not recorded"))

    col4, col5 = st.columns(2)

    col4.metric("Race", demographics.get("race", "Not recorded"))

    col5.metric(

        "Total Hospital Encounters",

        patient.get("total_encounters", 0)

    )

    st.markdown("---")

    st.markdown("## 📋 Hospital Encounter History")

    if not encounters:

        st.info("No encounters available.")

        return

    for index, encounter in enumerate(encounters, start=1):

        encounter_id = encounter.get("encounter_id", "N/A")

        with st.expander(

            f"Encounter {index} | ID: {encounter_id}",

            expanded=(index == 1)

        ):

            admission = encounter.get("admission", {})

            diagnosis = encounter.get("diagnosis", {})

            medication = encounter.get("medication", {})

            tab1, tab2, tab3 = st.tabs([

                "🏥 Admission Details",

                "🩺 Diagnosis Details",

                "💊 Medication Details"

            ])

            with tab1:

                st.markdown("### Hospital Admission Information")

                if admission:

                    admission_rows = [

                        (

                            ADMISSION_LABELS.get(

                                key, key.replace("_", " ").title()

                            ),

                            readable_value(key, value, id_mappings)

                        )

                        for key, value in admission.items()

                    ]

                    admission_df = pd.DataFrame(

                        admission_rows,

                        columns=["Medical Information", "Recorded Value"]

                    )

                    st.dataframe(

                        admission_df,

                        use_container_width=True,

                        hide_index=True

                    )

                else:

                    st.info("No admission information available.")

            with tab2:

                st.markdown("### Diagnosis Information")

                if diagnosis:

                    diagnosis_rows = []

                    for key, value in diagnosis.items():

                        label = DIAGNOSIS_LABELS.get(key, key.replace("_", " ").title())

                        if key in ("diag_1", "diag_2", "diag_3"):

                            description, status = diagnosis_code_details(value, diagnosis_mappings)

                            original = str(value).strip() if value is not None else "Not recorded"

                            diagnosis_rows.append((label, original, description, status))

                        else:

                            diagnosis_rows.append((label, readable_value(key, value, id_mappings), "", ""))

                    diagnosis_df = pd.DataFrame(

                        diagnosis_rows,

                        columns=["Diagnosis Information", "Original Code / Value", "Description", "Mapping Status"]

                    )

                    st.dataframe(diagnosis_df, use_container_width=True, hide_index=True)

                    st.caption(

                        "Exact descriptions come from the CMS ICD-9-CM Version 32 lookup. "

                        "No more-specific diagnosis is inferred from a broader code."

                    )

                else:

                    st.info("No diagnosis information available.")

            with tab3:

                st.markdown("### Medication Information")

                if medication:

                    # Summary fields describe the overall diabetes treatment,

                    # while the remaining fields describe individual medicines.

                    summary_col1, summary_col2 = st.columns(2)

                    summary_col1.metric(

                        "Diabetes Medication Prescribed",

                        medication_value("diabetesMed", medication.get("diabetesMed", "Not recorded"))

                    )

                    summary_col2.metric(

                        "Medication Regimen Change",

                        medication_value("change", medication.get("change", "Not recorded"))

                    )

                    individual_medications = [

                        (medication_label(key), medication_value(key, value))

                        for key, value in medication.items()

                        if key not in ("change", "diabetesMed")

                    ]

                    if individual_medications:

                        medication_df = pd.DataFrame(

                            individual_medications,

                            columns=["Medication", "Treatment Status"]

                        )

                        st.markdown("#### Individual Medication Details")

                        st.dataframe(

                            medication_df,

                            use_container_width=True,

                            hide_index=True

                        )

                    else:

                        st.info("No individual medication details are available.")

                    st.caption(

                        "Medication statuses are displayed using the source dataset values: "

                        "Steady = dosage unchanged, Up = dosage increased, Down = dosage decreased, "

                        "and No = medication not prescribed. Summary fields are shown separately."

                    )

                else:

                    st.info("No medication information available.")

# =====================================================

# DASHBOARD PAGE

# =====================================================

if page == "Dashboard":

    st.title("📊 Healthcare Analytics Dashboard")

    st.write(

        "Explore patient demographics, hospital encounters "

        "and readmission statistics. Use the filters below to refine the analysis."

    )

    try:

        patients, admissions, diagnoses, medications = load_datasets()

        # -------------------------------------------------

        # INTERACTIVE FILTERS

        # -------------------------------------------------

        st.markdown("### 🎛️ Dashboard Filters")

        age_order = [

            "[0-10)", "[10-20)", "[20-30)", "[30-40)",

            "[40-50)", "[50-60)", "[60-70)", "[70-80)",

            "[80-90)", "[90-100)"

        ]

        available_ages = [

            age for age in age_order if age in patients["age"].dropna().unique()

        ]

        available_genders = sorted(patients["gender"].dropna().astype(str).unique())

        available_races = sorted(

            patients["race"].fillna("Unknown").replace("?", "Unknown").astype(str).unique()

        )

        readmission_labels = {

            "NO": "Not Readmitted",

            ">30": "Readmitted After 30 Days",

            "<30": "Readmitted Within 30 Days"

        }

        available_readmissions = [

            value for value in ["NO", ">30", "<30"]

            if value in admissions["readmitted"].dropna().astype(str).unique()

        ]

        filter_col1, filter_col2 = st.columns(2)

        filter_col3, filter_col4 = st.columns(2)

        with filter_col1:

            selected_ages = st.multiselect(

                "Age Group",

                options=available_ages,

                default=available_ages,

                key="dashboard_age_filter"

            )

        with filter_col2:

            selected_genders = st.multiselect(

                "Gender",

                options=available_genders,

                default=available_genders,

                key="dashboard_gender_filter"

            )

        with filter_col3:

            selected_races = st.multiselect(

                "Race",

                options=available_races,

                default=available_races,

                key="dashboard_race_filter"

            )

        with filter_col4:

            selected_readmissions = st.multiselect(

                "Readmission Status",

                options=available_readmissions,

                default=available_readmissions,

                format_func=lambda value: readmission_labels.get(value, value),

                key="dashboard_readmission_filter"

            )

        # Apply patient-level demographic filters first.

        filtered_patients = patients[

            patients["age"].isin(selected_ages)

            & patients["gender"].astype(str).isin(selected_genders)

            & patients["race"].fillna("Unknown").replace("?", "Unknown").astype(str).isin(selected_races)

        ].copy()

        # Keep only encounters belonging to the selected patients.

        filtered_admissions = admissions[

            admissions["patient_nbr"].isin(filtered_patients["patient_nbr"])

            & admissions["readmitted"].astype(str).isin(selected_readmissions)

        ].copy()

        # Keep patient profile counts consistent with the encounters included.

        selected_patient_ids = filtered_admissions["patient_nbr"].unique()

        filtered_patients = filtered_patients[

            filtered_patients["patient_nbr"].isin(selected_patient_ids)

        ].copy()

        selected_encounter_ids = filtered_admissions["encounter_id"].unique()

        filtered_diagnoses = diagnoses[

            diagnoses["encounter_id"].isin(selected_encounter_ids)

        ].copy()

        filtered_medications = medications[

            medications["encounter_id"].isin(selected_encounter_ids)

        ].copy()

        st.caption(

            f"Showing {len(filtered_patients):,} patients and "

            f"{len(filtered_admissions):,} hospital encounters matching the selected filters."

        )

        if filtered_patients.empty or filtered_admissions.empty:

            st.warning("No records match the selected filters. Please broaden your selection.")

        else:

            # -------------------------------------------------

            # KEY PERFORMANCE INDICATORS

            # -------------------------------------------------

            total_patients = filtered_patients["patient_nbr"].nunique()

            total_encounters = filtered_admissions["encounter_id"].nunique()

            average_stay = filtered_admissions["time_in_hospital"].mean()

            encounters_per_patient = (

                filtered_admissions.groupby("patient_nbr")["encounter_id"].nunique()

            )

            multiple_encounters = int((encounters_per_patient > 1).sum())

            st.markdown("### 📌 Key Performance Indicators")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total Patients", f"{total_patients:,}")

            col2.metric("Total Hospital Encounters", f"{total_encounters:,}")

            col3.metric("Average Hospital Stay", f"{average_stay:.2f} days")

            col4.metric(

                "Patients with Multiple Encounters",

                f"{multiple_encounters:,}"

            )

            st.markdown("---")

            # -------------------------------------------------

            # PATIENT DEMOGRAPHICS

            # -------------------------------------------------

            st.markdown("### 👥 Patient Demographics")

            col1, col2 = st.columns(2)

            with col1:

                gender_data = (

                    filtered_patients["gender"]

                    .fillna("Not recorded")

                    .value_counts()

                    .rename_axis("Gender")

                    .reset_index(name="Number of Patients")

                )

                fig_gender = px.pie(

                    gender_data,

                    names="Gender",

                    values="Number of Patients",

                    title="Gender Distribution",

                    hole=0.45

                )

                st.plotly_chart(fig_gender, use_container_width=True)

            with col2:

                age_data = (

                    filtered_patients["age"]

                    .fillna("Not recorded")

                    .value_counts()

                    .reindex(available_ages, fill_value=0)

                    .rename_axis("Age Group")

                    .reset_index(name="Number of Patients")

                )

                fig_age = px.bar(

                    age_data,

                    x="Age Group",

                    y="Number of Patients",

                    title="Patient Distribution by Age Group",

                    text="Number of Patients"

                )

                st.plotly_chart(fig_age, use_container_width=True)

            # -------------------------------------------------

            # RACE DISTRIBUTION

            # -------------------------------------------------

            st.markdown("### 🌍 Patient Distribution by Race")

            race_data = (

                filtered_patients["race"]

                .fillna("Unknown")

                .replace("?", "Unknown")

                .value_counts()

                .rename_axis("Race")

                .reset_index(name="Number of Patients")

            )

            fig_race = px.bar(

                race_data,

                x="Race",

                y="Number of Patients",

                title="Patient Distribution by Race",

                text="Number of Patients"

            )

            st.plotly_chart(fig_race, use_container_width=True)

            st.markdown("---")

            # -------------------------------------------------

            # HOSPITAL ANALYTICS

            # -------------------------------------------------

            st.markdown("### 🏥 Hospital Analytics")

            col1, col2 = st.columns(2)

            with col1:

                readmission_data = (

                    filtered_admissions["readmitted"]

                    .astype(str)

                    .value_counts()

                    .reindex(["NO", ">30", "<30"], fill_value=0)

                    .rename_axis("Readmission Status")

                    .reset_index(name="Number of Encounters")

                )

                readmission_data["Readmission Status"] = (

                    readmission_data["Readmission Status"].replace({

                        "NO": "Not Readmitted",

                        ">30": "Readmitted After 30 Days",

                        "<30": "Readmitted Within 30 Days"

                    })

                )

                fig_readmission = px.pie(

                    readmission_data,

                    names="Readmission Status",

                    values="Number of Encounters",

                    title="Hospital Readmission Distribution",

                    hole=0.45

                )

                st.plotly_chart(fig_readmission, use_container_width=True)

            with col2:

                stay_data = (

                    filtered_admissions["time_in_hospital"]

                    .value_counts()

                    .sort_index()

                    .rename_axis("Hospital Stay (Days)")

                    .reset_index(name="Number of Encounters")

                )

                fig_stay = px.bar(

                    stay_data,

                    x="Hospital Stay (Days)",

                    y="Number of Encounters",

                    title="Hospital Stay Distribution",

                    text="Number of Encounters"

                )

                st.plotly_chart(fig_stay, use_container_width=True)

            st.markdown("---")

            # -------------------------------------------------

            # DIAGNOSIS ANALYTICS

            # -------------------------------------------------

            st.markdown("### 🩺 Diagnosis Analytics")

            primary_diagnoses = (

                filtered_diagnoses["diag_1"]

                .dropna()

                .astype(str)

                .str.strip()

            )

            primary_diagnoses = primary_diagnoses[

                ~primary_diagnoses.isin(["", "?", "nan", "NaN"])

            ]

            diagnosis_counts = (

                primary_diagnoses.value_counts().head(10)

                .rename_axis("Primary Diagnosis Code")

                .reset_index(name="Number of Encounters")

            )

            if not diagnosis_counts.empty:

                fig_diagnosis = px.bar(

                    diagnosis_counts,

                    x="Number of Encounters",

                    y="Primary Diagnosis Code",

                    orientation="h",

                    title="Top 10 Primary Diagnoses",

                    text="Number of Encounters"

                )

                fig_diagnosis.update_layout(

                    yaxis={"type": "category", "categoryorder": "total ascending"}

                )

                st.plotly_chart(fig_diagnosis, use_container_width=True)

            else:

                st.info("No diagnosis codes are available for these filters.")

            st.caption(

                "Diagnosis codes are displayed as recorded in the dataset; "

                "they are not clinical interpretations."

            )

            st.markdown("---")

            # -------------------------------------------------

            # MEDICATION ANALYTICS

            # -------------------------------------------------

            st.markdown("### 💊 Medication Analytics")

            medication_columns = [

                column for column in filtered_medications.columns

                if column not in ["encounter_id", "change", "diabetesMed"]

            ]

            medication_counts = (

                filtered_medications[medication_columns]

                .eq("Steady")

                .sum()

                .sort_values(ascending=False)

                .head(10)

                .rename_axis("Medication")

                .reset_index(name="Encounters with Steady Status")

            )

            fig_medication = px.bar(

                medication_counts,

                x="Medication",

                y="Encounters with Steady Status",

                title="Top 10 Medications with Steady Treatment Status",

                text="Encounters with Steady Status"

            )

            fig_medication.update_layout(xaxis_tickangle=-35)

            st.plotly_chart(fig_medication, use_container_width=True)

    except FileNotFoundError as error:

        st.error(

            "A required processed dataset file could not be found. "

            "Check DATA_PATH and confirm that all processed CSV files exist."

        )

        st.exception(error)

    except Exception as error:

        st.error("Unable to load dashboard analytics.")

        st.exception(error)

# =====================================================

# PATIENT SEARCH PAGE

# =====================================================

elif page == "Patient Search":

    st.title("🔍 Patient Search")

    st.write(

        "Enter a Patient ID to retrieve their complete medical records."

    )

    with st.form("patient_search_form"):

        patient_id = st.text_input(

            "Patient ID",

            placeholder="Example: 100000170"

        )

        search_button = st.form_submit_button(

            "Search Patient",

            use_container_width=True

        )

    if search_button:

        if not patient_id.strip():

            st.warning("Please enter a Patient ID.")

        elif not patient_id.strip().isdigit():

            st.warning("Patient ID must contain digits only.")

        else:

            with st.spinner("Retrieving patient records from HBase..."):

                patient, error = fetch_patient(patient_id.strip())

            if error:

                st.error(error)

            else:

                id_mappings = load_id_mappings()

                diagnosis_mappings = load_diagnosis_mappings()

                display_patient(patient, id_mappings, diagnosis_mappings)

                if not id_mappings:

                    st.info(

                        "IDS_mapping.csv was not found. Admission type, "

                        "source and discharge values are shown as original codes."

                    )

# =====================================================

# FOOTER

# =====================================================

st.markdown("---")

st.caption(

    "Patient Health Records Management System | "

    "Powered by Java, Apache HBase and Streamlit | "

    "Research dataset demonstration"

)
