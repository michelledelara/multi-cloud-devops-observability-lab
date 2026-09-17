import io
import json
import logging
import unittest
from prometheus_client.parser import text_string_to_metric_families
from app.main import create_app


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "LOG_DIR": "", "ENABLE_FAULTS": False})
        self.client = self.app.test_client()

    def samples(self):
        body = self.client.get("/metrics").text
        return [s for family in text_string_to_metric_families(body) for s in family.samples]

    def test_health_does_not_pollute_business_metrics(self):
        for route in ["/healthz", "/readyz", "/metrics"]:
            self.assertEqual(self.client.get(route).status_code, 200)
        self.assertFalse(any(s.name == "lab_http_requests_total" for s in self.samples()))

    def test_work_records_counter_and_latency(self):
        self.assertEqual(self.client.get("/work?delay_ms=1").status_code, 200)
        samples = self.samples()
        self.assertTrue(any(s.name == "lab_http_requests_total" and s.labels["route"] == "/work" and s.value == 1 for s in samples))
        self.assertTrue(any(s.name == "lab_http_request_duration_seconds_count" and s.value == 1 for s in samples))
        self.assertTrue(any(s.name == "lab_http_requests_in_progress" and s.value == 0 for s in samples))

    def test_delay_rejects_invalid_unbounded_and_nonfinite_inputs(self):
        for value in ["-1", "2001", "abc", "nan", "inf", "-inf"]:
            with self.subTest(value=value):
                self.assertEqual(self.client.get(f"/work?delay_ms={value}").status_code, 400)

    def test_unknown_paths_share_one_label(self):
        self.client.get("/unknown-1")
        self.client.get("/unknown-2")
        series = [s for s in self.samples() if s.name == "lab_http_requests_total"]
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0].labels["route"], "unmatched")
        self.assertEqual(series[0].value, 2)

    def test_fault_injection_is_opt_in(self):
        self.assertEqual(self.client.get("/fail").status_code, 403)
        self.app.config["ENABLE_FAULTS"] = True
        self.assertEqual(self.client.get("/fail").status_code, 500)
        self.assertTrue(any(s.name == "lab_http_requests_total" and s.labels["status"] == "500" for s in self.samples()))

    def test_logs_are_json_and_do_not_include_query_secrets(self):
        stream = io.StringIO()
        self.app.extensions["structured_logger"].addHandler(logging.StreamHandler(stream))
        response = self.client.get("/work?token=private-example")
        entry = json.loads(stream.getvalue())
        self.assertEqual(entry["request_id"], response.headers["X-Request-ID"])
        self.assertEqual(entry["route"], "/work")
        self.assertNotIn("private-example", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
