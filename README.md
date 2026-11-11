# Patient Health Records Management System

A big-data healthcare records application built with **Hadoop, HBase, Java, and Streamlit**. The system stores patient and encounter information in HBase, exposes it through a Java HTTP API, and provides a Streamlit interface for patient lookup and interactive analytics.

> **Project purpose:** Academic demonstration of distributed data storage, key-based retrieval, backend API integration, and dashboard-based analysis. This application is not intended for clinical diagnosis or treatment decisions.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [HBase Data Model](#hbase-data-model)
- [Dataset](#dataset)
- [Project Components](#project-components)
- [Prerequisites](#prerequisites)
- [Running the Project on Windows](#running-the-project-on-windows)
- [API Endpoints](#api-endpoints)
- [Diagnosis Mapping](#diagnosis-mapping)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

## Overview

The Patient Health Records Management System organizes healthcare encounter data into HBase tables to support efficient patient-centric retrieval. A Java HTTP server communicates with HBase and provides JSON responses to the frontend. The Streamlit application consumes those endpoints and presents patient records and analytical summaries through an interactive interface.

The application supports patients with multiple encounters. A patient search can retrieve the patient's available demographic information and associated encounter-level admission, diagnosis, and medication details.

## Key Features

- Patient lookup using a patient ID.
- Retrieval of patient demographic information.
- Retrieval of multiple encounters associated with a patient.
- Separate presentation of admission, diagnosis, and medication information.
- Readable labels for supported admission and discharge codes.
- Diagnosis descriptions for codes available in the diagnosis mapping file; unmapped codes remain available as codes.
- Medication status presentation, including whether diabetes medication was prescribed and whether the regimen changed.
- Interactive dashboard with filters and summary KPIs.
- Charts for exploring available dataset attributes.
- Friendly handling of patient IDs that are not present in the system.

## Technology Stack

| Component | Technology |
|---|---|
| Distributed storage ecosystem | Apache Hadoop |
| NoSQL database | Apache HBase |
| Backend/API | Java HTTP server |
| Frontend and dashboard | Streamlit |
| Data processing | Python, Pandas |
| Dataset format | CSV |
| Operating environment used for development | Windows |

Versions used during development:

- Hadoop 3.2.4
- HBase 2.5.16
- Java 8
- Streamlit (installed in the Python environment)

## System Architecture

```text
                 User
                  |
                  v
        Streamlit Frontend
          (Python, :8501)
                  |
             HTTP + JSON
                  |
                  v
         Java HTTP Server
              (:8080)
                  |
                  v
          PatientService
                  |
             HBase Client
                  |
                  v
       Apache HBase Database
          (5 application tables)
                  |
                  v
       Hadoop storage ecosystem
```

**Request flow**

1. The user enters a patient ID or interacts with the dashboard.
2. Streamlit sends a request to the Java HTTP API.
3. The Java backend uses `PatientService` and the HBase client to retrieve the requested data.
4. The backend returns the result as JSON.
5. Streamlit formats the response into patient details, encounter information, tables, metrics, and charts.

## HBase Data Model

The application uses the `patient_health` namespace and five tables.

| HBase table | Column family | Purpose |
|---|---|---|
| `patient_health:patient_records` | `personal` | Patient-level demographic information |
| `patient_health:admission_records` | `admission` | Encounter/admission-level information |
| `patient_health:diagnosis_records` | `diagnosis` | Diagnosis codes associated with encounters |
| `patient_health:medication_records` | `medication` | Medication-related information for encounters |
| `patient_health:patient_index` | `encounters` | Patient-to-encounter lookup information |

The design separates patient-level information from encounter-level information. The patient index supports finding the encounters associated with a patient, while the other tables hold the corresponding record details.

## Dataset

The project uses the **Diabetes 130-US Hospitals for Years 1999–2008** dataset made available through the UCI Machine Learning Repository.

Dataset scale used in this project:

- **101,766** hospital encounters.
- **71,518** unique patients.
- **16,773** patients with multiple encounters.

The source data contains demographic attributes and encounter-related admission, diagnosis, and medication fields. The project preprocesses the CSV data before loading it into HBase.

The dataset uses de-identified records. Values represented as missing or unknown in the source data should not be interpreted as confirmed clinical facts.

## Project Components

The project is organized into three main application components:

### 1. Data preparation and HBase storage

- Reads and preprocesses the source CSV files.
- Separates patient-level and encounter-level information.
- Creates and populates the five HBase tables.
- Maintains an index that connects a patient ID to its encounter IDs.

### 2. Java backend

- Connects to HBase.
- Retrieves patient and encounter records.
- Exposes HTTP endpoints that return JSON.
- Keeps database access separate from the Streamlit presentation layer.

### 3. Streamlit frontend

- Calls the Java API.
- Provides patient search and encounter views.
- Displays admission, diagnosis, and medication details.
- Provides dashboard filters, KPIs, and charts.

## Prerequisites

The following software should be installed and configured:

- Windows
- Java Development Kit 8
- Apache Hadoop 3.2.4
- Apache HBase 2.5.16
- Python
- Streamlit and the Python packages imported by the frontend
- The project's Java backend dependencies

The commands below use the development locations from this project. If the software is installed in different directories, update the paths accordingly.

## Running the Project on Windows

Open separate Command Prompt windows for the services that need to remain running. Start the services in the order below.

### 1. Start Hadoop

In a new Command Prompt:

```cmd
set "JAVA_HOME=C:\Java\jdk1.8.0_501"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d C:\hadoopsetup\hadoop-3.2.4\sbin
start-dfs.cmd
start-yarn.cmd
```

### 2. Start HBase

Open another Command Prompt:

```cmd
set "JAVA_HOME=C:\Java\jdk1.8.0_501"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d C:\hbasesetup\hbase-2.5.16\bin
start-hbase.cmd
```

Wait for HBase to finish starting before launching the backend.

### 3. Start the Java HTTP server

Open another Command Prompt:

```cmd
set "JAVA_HOME=C:\Java\jdk1.8.0_501"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d C:\PatientHealthRecords\java-backend
java -cp "target\classes;target\dependency\*" PatientHttpServer
```

Keep this window open while using the application.

### 4. Start the Streamlit frontend

Open another Command Prompt:

```cmd
cd /d C:\PatientHealthRecords\streamlit-frontend
streamlit run app.py
```

Streamlit normally displays a local address in the terminal, commonly:

```text
http://localhost:8501
```

Open the displayed local address in a browser.

### Service order

Start the components in this order:

1. Hadoop (HDFS and YARN)
2. HBase
3. Java HTTP server
4. Streamlit frontend

Do not run HBase schema initialization commands as part of every normal startup. Schema initialization is a one-time setup operation for a new database environment, not a routine start command.

## API Endpoints

The Java backend exposes the following endpoints used during development:

| Endpoint | Purpose |
|---|---|
| `/api/health` | Checks whether the backend API is responding |
| `/api/patient?patientId=<ID>` | Retrieves the patient record and associated information for the supplied patient ID |

Example local requests:

```text
http://localhost:8080/api/health
http://localhost:8080/api/patient?patientId=100000170
```

The patient ID above is a development test example. Use a patient ID present in the loaded dataset when testing another environment.

## Diagnosis Mapping

Diagnosis codes are stored in the diagnosis records. The frontend uses the project's `diagnosis_mapping_final.csv` file to display descriptions for codes that have a supported mapping.

The mapping distinguishes between:

- **Exact:** a code with an exact description in the selected ICD-9-CM reference.
- **Category:** a broader category-level description.
- **Unavailable:** a description is not supplied when a safe mapping is not available.

An unavailable description does not mean the diagnosis record is missing. The original diagnosis code can still be displayed. Category-level descriptions should be understood as broader labels, not as a more specific clinical interpretation.

The mapping file is expected at:

```text
C:\PatientHealthRecords\dataset\diagnosis_mapping_final.csv
```

## Limitations

- The application is an academic prototype and is not a production electronic health record system.
- The dataset is historical and does not represent current hospital activity.
- Some diagnosis codes do not have a mapped description in the current mapping file.
- The application should not be used to make clinical decisions.
- The current setup is a local development deployment; production use would require authentication, authorization, encryption, auditing, backup, monitoring, and appropriate healthcare data governance.

## Future Improvements

- Expand diagnosis description coverage using validated code references.
- Add authentication and role-based access control.
- Add audit logging for patient-record access.
- Improve deployment automation and service monitoring.
- Add more analytical views and configurable reports.
- Introduce automated tests for API responses and frontend workflows.

---

## Academic Use

This project demonstrates the integration of Hadoop ecosystem technologies, HBase wide-column storage, a Java-based API layer, and a Streamlit analytics interface for patient-centric healthcare data retrieval.
