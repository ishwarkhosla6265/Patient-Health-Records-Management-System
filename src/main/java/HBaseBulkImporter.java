import java.io.FileReader;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.io.InputStreamReader;
import java.io.FileInputStream;

import java.util.Map;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.BufferedMutator;
import org.apache.hadoop.hbase.client.BufferedMutatorParams;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.util.Bytes;

public class HBaseBulkImporter {

    private static final String DATA_PATH =
        "C:/PatientHealthRecords/dataset/processed/";

    private static final int BATCH_SIZE = 1000;

    private static long patientCount = 0;
    private static long admissionCount = 0;
    private static long diagnosisCount = 0;
    private static long medicationCount = 0;
    private static long indexCount = 0;

    private static boolean isValid(String value) {
        return value != null
            && !value.trim().isEmpty()
            && !value.trim().equals("?")
            && !value.trim().equalsIgnoreCase("nan");
    }

    private static BufferedMutator createMutator(
            Connection connection, String tableName) throws IOException {

        BufferedMutatorParams params =
            new BufferedMutatorParams(TableName.valueOf(tableName));

        params.writeBufferSize(4L * 1024 * 1024);

        return connection.getBufferedMutator(params);
    }

    private static long importRecords(
            String fileName,
            String tableName,
            String family,
            String rowKeyColumn,
            BufferedMutator mutator) throws Exception {

        long count = 0;

        String path = DATA_PATH + fileName;

        try (Reader reader = new InputStreamReader(
                 new FileInputStream(path), StandardCharsets.UTF_8);

             CSVParser parser = CSVFormat.DEFAULT.builder()
                 .setHeader()
                 .setSkipHeaderRecord(true)
                 .setTrim(true)
                 .build()
                 .parse(reader)) {

            for (CSVRecord record : parser) {

                String rowKey = record.get(rowKeyColumn);

                if (!isValid(rowKey)) {
                    continue;
                }

                Put put = new Put(Bytes.toBytes(rowKey));

                for (Map.Entry<String, Integer> entry :
                        parser.getHeaderMap().entrySet()) {

                    String column = entry.getKey();

                    if (column.equals(rowKeyColumn)) {
                        continue;
                    }

                    String value = record.get(column);

                    if (isValid(value)) {
                        put.addColumn(
                            Bytes.toBytes(family),
                            Bytes.toBytes(column),
                            Bytes.toBytes(value)
                        );
                    }
                }

                mutator.mutate(put);
                count++;

                if (count % BATCH_SIZE == 0) {
                    mutator.flush();

                    System.out.println(
                        tableName + " : " + count + " records imported"
                    );
                }
            }
        }

        mutator.flush();

        return count;
    }

    private static long importPatientIndex(
            BufferedMutator mutator) throws Exception {

        long count = 0;

        String path = DATA_PATH + "patient_index.csv";

        try (Reader reader = new InputStreamReader(
                 new FileInputStream(path), StandardCharsets.UTF_8);

             CSVParser parser = CSVFormat.DEFAULT.builder()
                 .setHeader()
                 .setSkipHeaderRecord(true)
                 .setTrim(true)
                 .build()
                 .parse(reader)) {

            for (CSVRecord record : parser) {

                String patientId = record.get("patient_nbr");
                String encounterIds = record.get("encounter_id");

                if (!isValid(patientId) || !isValid(encounterIds)) {
                    continue;
                }

                Put put = new Put(Bytes.toBytes(patientId));

                String[] ids = encounterIds.split(",");

                for (String encounterId : ids) {

                    if (isValid(encounterId)) {

                        put.addColumn(
                            Bytes.toBytes("encounters"),
                            Bytes.toBytes(encounterId.trim()),
                            Bytes.toBytes("1")
                        );
                    }
                }

                mutator.mutate(put);
                count++;

                if (count % BATCH_SIZE == 0) {
                    mutator.flush();

                    System.out.println(
                        "Patient Index : " + count + " records imported"
                    );
                }
            }
        }

        mutator.flush();

        return count;
    }

    public static void main(String[] args) {

        Configuration config = HBaseConfiguration.create();

        try (Connection connection =
                 ConnectionFactory.createConnection(config);

             BufferedMutator patients = createMutator(
                 connection, "patient_health:patient_records");

             BufferedMutator admissions = createMutator(
                 connection, "patient_health:admission_records");

             BufferedMutator diagnoses = createMutator(
                 connection, "patient_health:diagnosis_records");

             BufferedMutator medications = createMutator(
                 connection, "patient_health:medication_records");

             BufferedMutator patientIndex = createMutator(
                 connection, "patient_health:patient_index")) {

            System.out.println("==================================");
            System.out.println(" HBASE BULK IMPORT STARTED");
            System.out.println("==================================");

            patientCount = importRecords(
                "patients.csv",
                "patient_health:patient_records",
                "personal",
                "patient_nbr",
                patients
            );

            admissionCount = importRecords(
                "admissions.csv",
                "patient_health:admission_records",
                "admission",
                "encounter_id",
                admissions
            );

            diagnosisCount = importRecords(
                "diagnoses.csv",
                "patient_health:diagnosis_records",
                "diagnosis",
                "encounter_id",
                diagnoses
            );

            medicationCount = importRecords(
                "medications.csv",
                "patient_health:medication_records",
                "medication",
                "encounter_id",
                medications
            );

            indexCount = importPatientIndex(patientIndex);

            System.out.println("\n==================================");
            System.out.println(" BULK IMPORT COMPLETED");
            System.out.println("==================================");

            System.out.println("Patients imported: " + patientCount);
            System.out.println("Admissions imported: " + admissionCount);
            System.out.println("Diagnoses imported: " + diagnosisCount);
            System.out.println("Medications imported: " + medicationCount);
            System.out.println("Patient indexes imported: " + indexCount);

            System.out.println("==================================");

        } catch (Exception e) {
            System.err.println("BULK IMPORT FAILED!");
            e.printStackTrace();
        }
    }
}