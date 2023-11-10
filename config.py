import os

mqtt_host = os.environ.get("LOCAL_MQTT_HOST", "localhost")
mqtt_port = os.environ.get("LOCAL_MQTT_PORT", "1883")
mqtt_username = os.environ.get("LOCAL_MQTT_USERNAME", "")
mqtt_password = os.environ.get("LOCAL_MQTT_PASSWORD", "")

robot_hostname = os.environ.get("ROBOT_HOSTNAME", "localhost")
robot_port = os.environ.get("ROBOT_PORT", "3000")
robot_default_process_id = os.environ.get("ROBOT_DEFAULT_PROCESS_ID", "1")
robot_refresh_timeout = os.environ.get("ROBOT_REFRESH_TIMEOUT", "60")
