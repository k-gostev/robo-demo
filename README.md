# robo-demo

This is an adapter between a demo Robot API and a Ditto feature. This adapter is developed to be used with [Eclipse Kanto](https://eclipse.dev/kanto).
When it is connected to the local MQTT broker that is being used by Kanto, a cloud connector of your choice will create a digital twin of the robot on the cloud backend.

## Prerequisites: 
1. Install dependencies using:

    ```commandline
    pip3 install -r requirements.txt
    ```

2. Depending on your git version you may need to run

    ```commandline
    git submodule update --init --recursive
    ```

3. Install Eclipse Ditto
 
    ```commandline
    cd lib/ditto-clients && make install      
    ```

## Build:
Before building, you may need to change the platform to match your device.
```commandline
docker build -t 'your repo'/robot-controller:'tag' .              
```

## Deploy on Eclipse Kanto
1. [Install eclise Kanto](https://eclipse.dev/kanto/docs/getting-started/install/
2. Run the container using minimum configuration and host network.
```commandline
kanto-cm create -n robot-controller --network host  docker.io/'your container repo'/robot-controller:0.0.1
kanto-cm start -n robot-controller
```

Example using environment variable

```commandline
kanto-cm create -n robot-controller --network host --e=ROBOT_HOSTNAME=roboendpoint docker.io/'your container repo'/robot-controller:0.0.1
```

## Environment Variables

| Variable                 | Default   | Description                                                |
|--------------------------|-----------|------------------------------------------------------------|
| LOCAL_MQTT_HOST          | localhost | Local MQTT broker host name                                |
| LOCAL_MQTT_PORT          | 1883      | Local MQTT broker port                                     |
| LOCAL_MQTT_USERNAME      |           | Local MQTT broker username                                 |
| LOCAL_MQTT_PASSWORD      |           | Local MQTT broker password                                 |
| ROBOT_HOSTNAME           | localhost | Hostname of the robot's http endpoint                      |
| ROBOT_PORT               | 3000      | Port of the robot's http endpoint                          |
| ROBOT_DEFAULT_PROCESS_ID | 1         | Default process which will be triggered on command         |
|  ROBOT_REFRESH_TIMEOUT   | 60        | Refresh timeout on which the Ditto feature will be updated |

## Command Format

```json
{
    "topic": "demo/robot/things/live/commands/request",
    "headers": {
        "correlation-id": "test",
        "content-type": "application/json"
    },
      "path": "/features/Robo/inbox/messages/request",
      "value": {
            "program_id": 1,
            "iterations": 1,
            "velocity": 1
        }
    }
```
