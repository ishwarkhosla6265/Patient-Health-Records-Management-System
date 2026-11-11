import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.Get;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

public class HBaseConnection {

    public static void main(String[] args) {

        Configuration config = HBaseConfiguration.create();

        config.set("hbase.zookeeper.quorum", "localhost");
        config.set("hbase.zookeeper.property.clientPort", "2181");

        try (Connection connection = ConnectionFactory.createConnection(config)) {

            Table table = connection.getTable(
                TableName.valueOf("patient_health:patient_records")
            );

            Get get = new Get(Bytes.toBytes("P1001"));

            Result result = table.get(get);

            System.out.println("PATIENT DETAILS");
            System.out.println("--------------------------");

            System.out.println("Patient ID: P1001");
            System.out.println("Name: " +
                Bytes.toString(result.getValue(
                    Bytes.toBytes("personal"), Bytes.toBytes("name")
                ))
            );

            System.out.println("Age: " +
                Bytes.toString(result.getValue(
                    Bytes.toBytes("personal"), Bytes.toBytes("age")
                ))
            );

            System.out.println("Gender: " +
                Bytes.toString(result.getValue(
                    Bytes.toBytes("personal"), Bytes.toBytes("gender")
                ))
            );

            System.out.println("Blood Group: " +
                Bytes.toString(result.getValue(
                    Bytes.toBytes("clinical"), Bytes.toBytes("blood_group")
                ))
            );

            table.close();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}