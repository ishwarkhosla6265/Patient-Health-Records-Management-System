import java.util.Map;
import java.util.List;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.NavigableMap;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.*;
import org.apache.hadoop.hbase.util.Bytes;

public class PatientService {

    private static final String PATIENT_TABLE =
        "patient_health:patient_records";

    private static final String INDEX_TABLE =
        "patient_health:patient_index";

    private static final String ADMISSION_TABLE =
        "patient_health:admission_records";

    private static final String DIAGNOSIS_TABLE =
        "patient_health:diagnosis_records";

    private static final String MEDICATION_TABLE =
        "patient_health:medication_records";

    private static final byte[] PERSONAL =
        Bytes.toBytes("personal");

    private static final byte[] ENCOUNTERS =
        Bytes.toBytes("encounters");

    private static final byte[] ADMISSION =
        Bytes.toBytes("admission");

    private static final byte[] DIAGNOSIS =
        Bytes.toBytes("diagnosis");

    private static final byte[] MEDICATION =
        Bytes.toBytes("medication");


    private static Map<String, String> getFamilyData(
            Result result, byte[] family) {

        Map<String, String> data = new LinkedHashMap<>();

        NavigableMap<byte[], byte[]> values =
            result.getFamilyMap(family);

        if (values == null || values.isEmpty()) {
            return data;
        }

        for (Map.Entry<byte[], byte[]> entry : values.entrySet()) {

            String column = Bytes.toString(entry.getKey());
            String value = Bytes.toString(entry.getValue());

            data.put(column, value);
        }

        return data;
    }


    public static Map<String, Object> getPatient(
            Connection connection, String patientId) throws Exception {

        try (Table table = connection.getTable(
                TableName.valueOf(PATIENT_TABLE))) {

            Get get = new Get(Bytes.toBytes(patientId));

            Result result = table.get(get);

            if (result.isEmpty()) {
                return null;
            }

            Map<String, Object> patient = new LinkedHashMap<>();

            patient.put("patient_id", patientId);
            patient.put("demographics",
                getFamilyData(result, PERSONAL));

            return patient;
        }
    }


    public static List<String> getPatientEncounters(
            Connection connection, String patientId) throws Exception {

        List<String> encounterList = new ArrayList<>();

        try (Table table = connection.getTable(
                TableName.valueOf(INDEX_TABLE))) {

            Get get = new Get(Bytes.toBytes(patientId));

            Result result = table.get(get);

            if (result.isEmpty()) {
                return encounterList;
            }

            NavigableMap<byte[], byte[]> encounters =
                result.getFamilyMap(ENCOUNTERS);

            if (encounters == null || encounters.isEmpty()) {
                return encounterList;
            }

            for (byte[] encounterId : encounters.keySet()) {

                encounterList.add(Bytes.toString(encounterId));
            }
        }

        return encounterList;
    }


    public static Map<String, String> getAdmission(
            Connection connection, String encounterId) throws Exception {

        try (Table table = connection.getTable(
                TableName.valueOf(ADMISSION_TABLE))) {

            Get get = new Get(Bytes.toBytes(encounterId));

            Result result = table.get(get);

            if (result.isEmpty()) {
                return new LinkedHashMap<>();
            }

            return getFamilyData(result, ADMISSION);
        }
    }


    public static Map<String, String> getDiagnosis(
            Connection connection, String encounterId) throws Exception {

        try (Table table = connection.getTable(
                TableName.valueOf(DIAGNOSIS_TABLE))) {

            Get get = new Get(Bytes.toBytes(encounterId));

            Result result = table.get(get);

            if (result.isEmpty()) {
                return new LinkedHashMap<>();
            }

            return getFamilyData(result, DIAGNOSIS);
        }
    }


    public static Map<String, String> getMedication(
            Connection connection, String encounterId) throws Exception {

        try (Table table = connection.getTable(
                TableName.valueOf(MEDICATION_TABLE))) {

            Get get = new Get(Bytes.toBytes(encounterId));

            Result result = table.get(get);

            if (result.isEmpty()) {
                return new LinkedHashMap<>();
            }

            return getFamilyData(result, MEDICATION);
        }
    }


    public static Map<String, Object> getCompletePatientRecord(
            String patientId) throws Exception {

        Configuration config = HBaseConfiguration.create();

        try (Connection connection =
                 ConnectionFactory.createConnection(config)) {

            Map<String, Object> patient =
                getPatient(connection, patientId);

            if (patient == null) {
                return null;
            }

            List<String> encounterIds =
                getPatientEncounters(connection, patientId);

            List<Map<String, Object>> encounterRecords =
                new ArrayList<>();

            for (String encounterId : encounterIds) {

                Map<String, Object> encounter =
                    new LinkedHashMap<>();

                encounter.put("encounter_id", encounterId);

                encounter.put("admission",
                    getAdmission(connection, encounterId));

                encounter.put("diagnosis",
                    getDiagnosis(connection, encounterId));

                encounter.put("medication",
                    getMedication(connection, encounterId));

                encounterRecords.add(encounter);
            }

            patient.put("total_encounters", encounterRecords.size());

            patient.put("encounters", encounterRecords);

            return patient;
        }
    }


    public static void main(String[] args) throws Exception {

        String patientId = args.length > 0
            ? args[0]
            : "100000170";

        Map<String, Object> patient =
            getCompletePatientRecord(patientId);

        if (patient == null) {
            System.out.println("Patient not found!");
            return;
        }

        System.out.println(patient);
    }
}
