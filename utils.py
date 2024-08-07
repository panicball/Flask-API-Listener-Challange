from datetime import datetime
from typing import Dict, List, Any
import logging
import os


class LogValidationError(Exception):
    """Raised when log validation fails."""
    pass


# logging configuration
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# environment variable for LOG_DIRECTORY or fallback value
LOG_DIRECTORY = os.getenv('LOG_DIRECTORY', 'logs')


def is_numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class LogManager:
    def __init__(self, log_directory: str):
        self.log_directory = log_directory
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

    @staticmethod
    def get_next_id() -> int:
        """Get possible log ID."""
        existing_logs = [f for f in os.listdir(LOG_DIRECTORY) if f.endswith('.log')]
        return len(existing_logs) + 1

    @staticmethod
    def get_highest_log_id() -> int:
        """Get the highest existing log ID."""
        existing_logs = [f for f in os.listdir(LOG_DIRECTORY) if f.endswith('.log')]
        log_ids = []
        for log in existing_logs:
            log_ids.append(int(log.removeprefix("log_").removesuffix(".log")))
        return max(log_ids) + 1

    @staticmethod
    def request_body_formatting(body: str) -> str:
        """
        Format the request body for proper log entry
        by adding new line symbols after every log line.
        """
        first_timestamp_end = body.find(']') + 1
        first_part = body[:first_timestamp_end]
        rest = body[first_timestamp_end:]
        if '\n[' in rest:
            return body

        modified_rest = rest.replace('[', '\n[')
        return first_part + modified_rest

    @staticmethod
    def validate_log_entry(entry: str) -> bool:
        """
        Validate a single log entry. The log entry must have this
        structure -> "[2024-07-19 10:00:00] INFO: System started"
        """
        try:
            timestamp, rest = entry.split('] ', 1)
            timestamp = timestamp[1:]
            datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

            level, message = rest.split(': ', 1)

            # factually this might be incorrect as hardcoding is a big no no
            if level not in ['INFO', 'ERROR', 'MEASUREMENT', 'WARNING', 'DEBUG']:
                raise LogValidationError(f"Invalid log level: {level}")

            return True
        except (ValueError, IndexError, LogValidationError) as e:
            logging.error(f"Log validation failed: {str(e)}")
            return False

    @staticmethod
    def parse_log_content(valid_lines: List[str]) -> Dict[str, Any]:
        """
        Parse log content and extract relevant information.
        This function:
         1. counts different log levels;
         2. gets average, highest, lowest MEASUREMENTS values;
         3. counts alarms and returns their timestamps.
        """
        log_counts: Dict[str, int] = {'ERROR': 0, 'INFO': 0, 'MEASUREMENT': 0, 'WARNING': 0, 'DEBUG': 0}
        measurements: Dict[str, List[float]] = {}
        alarms: List[str] = []

        for line in valid_lines:
            timestamp, rest = line.split('] ', 1)
            timestamp = timestamp[1:]
            log_level, message = rest.split(': ', 1)
            log_counts[log_level] += 1

            if log_level == 'MEASUREMENT' and 'concentration' in message:
                parts = message.split('concentration')
                if len(parts) >= 2:
                    gas_type = parts[0].strip()
                    value_part = parts[1].split('-')[-1].strip()
                    if is_numeric(value_part):
                        gas_value = float(value_part)
                        measurements.setdefault(gas_type, []).append(gas_value)
                    else:
                        logging.warning(f"Invalid measurement value: {message}")
                else:
                    logging.warning(f"Malformed measurement message: {message}")
            elif log_level == 'WARNING' and 'alarm' in message.lower():
                alarms.append(timestamp)

        result = {
            "log_message_count": log_counts,
            "measurements": {},
            "alarms": {
                "count": len(alarms),
                "timestamps": alarms
            }
        }

        for gas, values in measurements.items():
            result["measurements"][gas] = {
                "average": sum(values) / len(values) if values else None,
                "highest": max(values) if values else None,
                "lowest": min(values) if values else None
            }

        return result
