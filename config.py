import os

mqtt_host = os.environ.get("LOCAL_MQTT_HOST", "localhost")
mqtt_port = os.environ.get("LOCAL_MQTT_PORT", "1883")
mqtt_username = os.environ.get("LOCAL_MQTT_USERNAME", "")
mqtt_password = os.environ.get("LOCAL_MQTT_PASSWORD", "")

device_id = os.getenv("DEVICE_ID", "demo:robot:1.0.0")

robot_hostname = os.environ.get("ROBOT_HOSTNAME", "localhost")
robot_port = os.environ.get("ROBOT_PORT", "10000")
robot_port_udp = os.environ.get("ROBOT_PORT_UDP", "10001")
robot_username = os.environ.get("ROBOT_USERNAME", "admin")
robot_password = os.environ.get("ROBOT_PASSWORD", "admin")
robot_default_process_id = os.environ.get("ROBOT_DEFAULT_PROCESS_ID", "1")
robot_refresh_timeout = os.environ.get("ROBOT_REFRESH_TIMEOUT", "60")
