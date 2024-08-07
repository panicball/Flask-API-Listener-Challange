import unittest
import json
import os
from app import app
from utils import LogManager, LOG_DIRECTORY


class FlaskAPITests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        self.test_log_dir = LOG_DIRECTORY
        if not os.path.exists(self.test_log_dir):
            os.makedirs(self.test_log_dir)

    def tearDown(self):
        for file in os.listdir(self.test_log_dir):
            os.remove(os.path.join(self.test_log_dir, file))
        os.rmdir(self.test_log_dir)

    def test_get_log_success(self):
        with open(f"{self.test_log_dir}/log_1.log", 'w') as f:
            f.write("Test log content")

        response = self.app.get('/get_log/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['content'], "Test log content")

    def test_get_log_not_found(self):
        response = self.app.get('/get_log/999')
        self.assertEqual(response.status_code, 404)

    def test_save_log_success(self):
        log_content = "[2024-07-19 10:00:00] INFO: Test log"
        response = self.app.post('/save_log', json={'content': log_content})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('id', data)

    def test_save_log_invalid_content(self):
        response = self.app.post('/save_log', json={'content': "Invalid log"})
        self.assertEqual(response.status_code, 400)

    def test_update_log_success(self):
        with open(f"{self.test_log_dir}/log_1.log", 'w') as f:
            f.write("[2024-07-19 10:00:00] INFO: Correct log")

        new_content = "[2024-07-19 10:01:00] INFO: Updated log"
        response = self.app.put('/update_log/1', json={'content': new_content})
        self.assertEqual(response.status_code, 200)

    def test_update_and_append_log_success(self):
        with open(f"{self.test_log_dir}/log_1.log", 'w') as f:
            f.write("[2024-07-19 10:00:00] INFO: First log line\n")

        new_content = "[2024-07-19 10:01:00] INFO: Second log line\n"
        response = self.app.put('/update_log/1?append=true',
                                json={'content': new_content})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], "Log file log_1.log updated successfully!")

        with open(f"{self.test_log_dir}/log_1.log", 'r') as f:
            content = f.read()

        expected_content = ("[2024-07-19 10:00:00] INFO: First log line\n"
                            "[2024-07-19 10:01:00] INFO: Second log line\n")
        self.assertEqual(content, expected_content)

    def test_update_and_overwrite_log_success(self):
        with open(f"{self.test_log_dir}/log_1.log", 'w') as f:
            f.write("[2024-07-19 10:00:00] INFO: First log line\n")

        self.app.put('/update_log/1?append=true',
                     json={'content': "[2024-07-19 10:01:00] INFO: Second log line\n"})

        response = self.app.put('/update_log/1?append=false',
                                json={'content': "[2024-07-19 10:01:00] INFO: Third log line\n"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], "Log file log_1.log updated successfully!")

        with open(f"{self.test_log_dir}/log_1.log", 'r') as f:
            content = f.read()

        expected_content = "[2024-07-19 10:01:00] INFO: Third log line\n"
        self.assertEqual(content, expected_content)

    def test_update_log_not_found(self):
        response = self.app.put('/update_log/999', json={'content': "Test"})
        self.assertEqual(response.status_code, 404)

    def test_delete_log_success(self):
        with open(f"{self.test_log_dir}/log_1.log", 'w') as f:
            f.write("Test log content")

        response = self.app.delete('/delete_log/1')
        self.assertEqual(response.status_code, 200)

    def test_delete_log_not_found(self):
        response = self.app.delete('/delete_log/999')
        self.assertEqual(response.status_code, 404)

    def test_parse_log_success(self):
        log_content = """
        [2024-07-19 10:00:00] INFO: System started
        [2024-07-19 10:02:00] ERROR: Failed to connect
        [2024-07-19 10:03:00] MEASUREMENT: o2 concentration - 25
        [2024-07-19 10:04:00] WARNING: Going to o2 alarm
        """
        response = self.app.post('/parse_log', json={'content': log_content})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('log_message_count', data)
        self.assertIn('measurements', data)
        self.assertIn('alarms', data)

    def test_parse_log_invalid_content(self):
        response = self.app.post('/parse_log', json={'content': "Invalid log"})
        self.assertEqual(response.status_code, 400)

    def test_get_next_id(self):
        for i in range(1, 4):
            open(f"{self.test_log_dir}/log_{i}.log", 'w').close()

        self.assertEqual(LogManager.get_next_id(), 4)

    def test_get_highest_log_id(self):
        open(f"{self.test_log_dir}/log_1.log", 'w').close()
        open(f"{self.test_log_dir}/log_5.log", 'w').close()
        open(f"{self.test_log_dir}/log_3.log", 'w').close()

        self.assertEqual(LogManager.get_highest_log_id(), 6)

    def test_request_body_formatting(self):
        input_body = "[2024-07-19 10:00:00] INFO: Test[2024-07-19 10:01:00] ERROR: Another test"
        expected_output = "[2024-07-19 10:00:00] INFO: Test\n[2024-07-19 10:01:00] ERROR: Another test"
        self.assertEqual(LogManager.request_body_formatting(input_body), expected_output)

    def test_validate_log_entry_valid(self):
        valid_entry = "[2024-07-19 10:00:00] INFO: System started"
        self.assertTrue(LogManager.validate_log_entry(valid_entry))

    def test_validate_log_entry_invalid_timestamp(self):
        invalid_entry = "[2024-07-19 25:00:00] INFO: Invalid timestamp"
        self.assertFalse(LogManager.validate_log_entry(invalid_entry))

    def test_validate_log_entry_invalid_level(self):
        invalid_entry = "[2024-07-19 10:00:00] INVALID: Wrong level"
        self.assertFalse(LogManager.validate_log_entry(invalid_entry))

    def test_validate_log_entry_malformed(self):
        malformed_entry = "This is not a valid log entry"
        self.assertFalse(LogManager.validate_log_entry(malformed_entry))

    def test_parse_log_content(self):
        log_data = [
            "[2024-07-19 10:00:00] INFO: System started",
            "[2024-07-19 10:01:00] ERROR: Connection failed",
            "[2024-07-19 10:02:00] MEASUREMENT: O2 concentration - 21.0",
            "[2024-07-19 10:03:00] WARNING: High temperature alarm",
            "[2024-07-19 10:04:00] DEBUG: Sensor check completed",
            "[2024-07-19 10:05:00] MEASUREMENT: CO2 concentration - 400.0",
            "[2024-07-19 10:06:00] MEASUREMENT: O2 concentration - 20.5",
            "[2024-07-19 10:07:00] WARNING: Low oxygen alarm",
            "[2024-07-19 10:08:00] MEASUREMENT: CO2 concentration - 450.0"
        ]
        result = LogManager.parse_log_content(log_data)

        self.assertEqual(result["log_message_count"], {
            'ERROR': 1,
            'INFO': 1,
            'MEASUREMENT': 4,
            'WARNING': 2,
            'DEBUG': 1
        })

        self.assertIn("O2", result["measurements"])
        self.assertIn("CO2", result["measurements"])

        o2_measurements = result["measurements"]["O2"]
        self.assertAlmostEqual(o2_measurements["average"], 20.75)
        self.assertAlmostEqual(o2_measurements["highest"], 21.0)
        self.assertAlmostEqual(o2_measurements["lowest"], 20.5)

        co2_measurements = result["measurements"]["CO2"]
        self.assertAlmostEqual(co2_measurements["average"], 425.0)
        self.assertAlmostEqual(co2_measurements["highest"], 450.0)
        self.assertAlmostEqual(co2_measurements["lowest"], 400.0)

        self.assertEqual(result["alarms"]["count"], 2)
        self.assertEqual(result["alarms"]["timestamps"], [
            "2024-07-19 10:03:00",
            "2024-07-19 10:07:00"
        ])

    def test_parse_log_content_empty_input(self):
        result = LogManager.parse_log_content([])

        self.assertEqual(result["log_message_count"], {
            'ERROR': 0,
            'INFO': 0,
            'MEASUREMENT': 0,
            'WARNING': 0,
            'DEBUG': 0
        })
        self.assertEqual(result["measurements"], {})
        self.assertEqual(result["alarms"]["count"], 0)
        self.assertEqual(result["alarms"]["timestamps"], [])

    def test_parse_log_content_no_measurements(self):
        log_data = [
            "[2024-07-19 10:00:00] INFO: System started",
            "[2024-07-19 10:01:00] ERROR: Connection failed",
            "[2024-07-19 10:03:00] WARNING: High temperature alarm"
        ]

        result = LogManager.parse_log_content(log_data)

        self.assertEqual(result["log_message_count"], {
            'ERROR': 1,
            'INFO': 1,
            'MEASUREMENT': 0,
            'WARNING': 1,
            'DEBUG': 0
        })
        self.assertEqual(result["measurements"], {})
        self.assertEqual(result["alarms"]["count"], 1)
        self.assertEqual(result["alarms"]["timestamps"], ["2024-07-19 10:03:00"])

    def test_parse_log_content_invalid_measurement(self):
        log_data = [
            "[2024-07-19 10:00:00] MEASUREMENT: Invalid concentration data"
        ]

        result = LogManager.parse_log_content(log_data)

        self.assertEqual(result["log_message_count"]["MEASUREMENT"], 1)
        self.assertEqual(result["measurements"], {})


if __name__ == '__main__':
    unittest.main()
