from flask import Flask, request, jsonify
import os
from utils import LogManager, LOG_DIRECTORY
import logging

app = Flask(__name__)
log_manager = LogManager(LOG_DIRECTORY)


@app.route('/get_log/<int:id>', methods=['GET'])
def get_log(id: int):
    filename = f"{LOG_DIRECTORY}/log_{id}.log"
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            content = file.read()
        logging.info(f"Retrieved log file with id {id}.")
        return jsonify({"id": id, "content": content}), 200
    logging.error(f"Log file with id {id} not found.")
    return jsonify({"error": "Log file not found."}), 404


@app.route('/save_log', methods=['POST'])
def save_log():
    data = request.json
    if not data or 'content' not in data:
        logging.error("No request body provided.")
        return jsonify({"error": "No request body provided."}), 400

    lines = log_manager.request_body_formatting(data['content']).split('\n')
    valid_lines = [line for line in lines if log_manager.validate_log_entry(line)]

    if not valid_lines:
        logging.error("No valid log file entries provided.")
        return jsonify({"error": "No valid log file entries provided."}), 400

    new_id = log_manager.get_next_id()
    filename = f"{LOG_DIRECTORY}/log_{new_id}.log"

    # check if filename already exists (to avoid overwriting)
    if os.path.exists(filename):
        new_id = log_manager.get_highest_log_id()
        filename = f"{LOG_DIRECTORY}/log_{new_id}.log"

    with open(filename, 'w') as file:
        file.write('\n'.join(valid_lines) + '\n')

    logging.info(f"Log file saved successfully! Filename log_{new_id}.log")
    return jsonify({"message": f"Log file saved successfully! Filename log_{new_id}.log", "id": new_id}), 200


@app.route('/update_log/<int:id>', methods=['PUT'])
def update_log(id: int):
    data = request.json
    if not data or 'content' not in data:
        logging.error("No request body provided. Nothing to update.")
        return jsonify({"error": "No request body provided."}), 400

    filename = f"{LOG_DIRECTORY}/log_{id}.log"
    if not os.path.exists(filename):
        logging.error(f"Log file not found. Filename log_{id}.log")
        return jsonify({"error": "Log file not found."}), 404

    lines = log_manager.request_body_formatting(data['content']).split('\n')
    valid_lines = [line for line in lines if log_manager.validate_log_entry(line)]

    if not valid_lines:
        logging.error("No valid log file entries provided.")
        return jsonify({"error": "No valid log file entries provided."}), 400

    append = request.args.get('append', 'false').lower() == 'true'
    mode = 'a' if append else 'w'

    with open(filename, mode) as file:
        file.write('\n'.join(valid_lines) + '\n')
    logging.info(f"Log file log_{id}.log updated successfully!")
    return jsonify({"message": f"Log file log_{id}.log updated successfully!"}), 200


@app.route('/delete_log/<int:id>', methods=['DELETE'])
def delete_log(id: int):
    filename = f"{LOG_DIRECTORY}/log_{id}.log"
    if os.path.exists(filename):
        os.remove(filename)
        logging.info(f"Log file log_{id}.log deleted.")
        return jsonify({"message": f"Log file log_{id}.log deleted."}), 200
    logging.error(f"Specified log file not found. Filename log_{id}.log")
    return jsonify({"error": "Specified log file not found."}), 404


@app.route('/parse_log', methods=['POST'])
@app.route('/parse_log/<int:log_id>', methods=['POST'])
def parse_log(log_id=None):
    if log_id is not None:
        filename = f"{LOG_DIRECTORY}/log_{log_id}.log"
        if not os.path.exists(filename):
            logging.error(f"Log file not found. Filename log_{log_id}.log")
            return jsonify({"error": "Log file not found."}), 404
        with open(filename, 'r') as file:
            content = file.read()
    else:
        data = request.json
        if not data or 'content' not in data:
            logging.error("Invalid request to parse log-type content.")
            return jsonify({"error": "Invalid request."}), 400
        content = data['content']

    lines = log_manager.request_body_formatting(content).split('\n')
    valid_lines = [line for line in lines if log_manager.validate_log_entry(line)]

    if not valid_lines:
        logging.error("No valid log file entries provided.")
        return jsonify({"error": "No valid log file entries provided."}), 400

    results = log_manager.parse_log_content(valid_lines)
    logging.info("Log parsed successfully")
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(debug=True)
