# Flask-API-Listener-Challange
Flask API listener that manipulates log data files.

## The mentioned app has following endpoints implemented:

### Retrieve a Log File
- **Endpoint:** `/get_log`
- **Method:** GET

### Create a New Log File
- **Endpoint:** `/save_log`
- **Method:** POST

### Modify an Existing Log File
- **Endpoint:** `/update_log`
- **Method:** PUT

### Remove a Log File
- **Endpoint:** `/delete_log`
- **Method:** DELETE

### Parse Log File Contents
- **Endpoint:** `/parse_log`
- **Method:** POST

Postman collection for the mentioned endpoint usage added.

## Running Flask App as a Windows Service
In order to run Flask application indefinitely on a Windows system, Windows Service Control Manager (SCM) is utilized. This approach allows the Flask app to run in the background and start automatically with Windows itself.

Flask application as a Windows service can be used by running the `flask_service.py` script.

### Installation
`python flask_service.py install`

### Starting the Service
`python flask_service.py start`

### Stopping Service
`python flask_service.py stop`

### Removing the service
`python flask_service.py remove`

## Testing
Flask API is used using `unittest`. Tests are used to verify various possible (in)correct scenarios that might occur while running the API.

### Running the tests
`python -m unittest test_app.py`
