import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.io.OutputStream;

import java.net.InetSocketAddress;
import java.net.URLDecoder;

import java.nio.charset.StandardCharsets;

import java.security.MessageDigest;

import java.util.Map;
import java.util.LinkedHashMap;
import java.util.concurrent.Executors;

public class PatientHttpServer {

    private static final int PORT = 8080;

    private static final String API_KEY =
        System.getenv("PATIENT_API_KEY");

    private static final ObjectMapper objectMapper =
        new ObjectMapper();

    public static void main(String[] args) throws Exception {

        if (API_KEY == null || API_KEY.trim().isEmpty()) {
            throw new IllegalStateException(
                "PATIENT_API_KEY environment variable is missing!"
            );
        }

        HttpServer server = HttpServer.create(
            new InetSocketAddress(PORT), 0
        );

        server.createContext("/api/health", new HealthHandler());

        server.createContext("/api/patient", new PatientHandler());

        server.setExecutor(Executors.newFixedThreadPool(10));

        server.start();

        System.out.println("==================================");
        System.out.println(" PATIENT HEALTH HTTP SERVER");
        System.out.println("==================================");
        System.out.println("Server running at http://localhost:" + PORT);
        System.out.println("Health: http://localhost:8080/api/health");
        System.out.println("Patient API: Protected with API key");
        System.out.println("==================================");
    }

    static class HealthHandler implements HttpHandler {

        @Override
        public void handle(HttpExchange exchange) throws IOException {

            Map<String, Object> response = new LinkedHashMap<>();

            response.put("status", "UP");
            response.put("message", "Patient Health API is running!");

            sendJson(exchange, 200, response);
        }
    }

    static class PatientHandler implements HttpHandler {

        @Override
        public void handle(HttpExchange exchange) throws IOException {

            if (!exchange.getRequestMethod().equals("GET")) {

                sendError(exchange, 405, "Method not allowed");
                return;
            }

            String suppliedKey =
                exchange.getRequestHeaders().getFirst("X-API-Key");

            if (suppliedKey == null ||
                !MessageDigest.isEqual(
                    API_KEY.getBytes(StandardCharsets.UTF_8),
                    suppliedKey.getBytes(StandardCharsets.UTF_8)
                )) {

                sendError(exchange, 401, "Unauthorized");
                return;
            }

            String query = exchange.getRequestURI().getRawQuery();

            if (query == null || query.trim().isEmpty()) {

                sendError(exchange, 400, "Patient ID is required");
                return;
            }

            String patientId = null;

            for (String parameter : query.split("&")) {

                String[] pair = parameter.split("=", 2);

                if (pair.length == 2 && pair[0].equals("patientId")) {

                    patientId = URLDecoder.decode(pair[1], "UTF-8");
                    break;
                }
            }

            if (patientId == null || patientId.trim().isEmpty()) {

                sendError(exchange, 400, "Invalid patient ID");
                return;
            }

            patientId = patientId.trim();

            try {

                Map<String, Object> patient =
                    PatientService.getCompletePatientRecord(patientId);

                if (patient == null) {

                    sendError(exchange, 404, "Patient not found");
                    return;
                }

                sendJson(exchange, 200, patient);

            } catch (Exception e) {

                e.printStackTrace();

                sendError(
                    exchange,
                    500,
                    "Internal server error while retrieving patient records"
                );
            }
        }
    }

    private static void sendError(
            HttpExchange exchange,
            int statusCode,
            String message) throws IOException {

        Map<String, Object> error = new LinkedHashMap<>();

        error.put("status", statusCode);
        error.put("error", message);

        sendJson(exchange, statusCode, error);
    }

    private static void sendJson(
            HttpExchange exchange,
            int statusCode,
            Object response) throws IOException {

        byte[] bytes = objectMapper
            .writeValueAsString(response)
            .getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().set(
            "Content-Type",
            "application/json; charset=UTF-8"
        );

        exchange.sendResponseHeaders(statusCode, bytes.length);

        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
