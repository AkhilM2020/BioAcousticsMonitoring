import paho.mqtt.client as mqtt
import os
from datetime import datetime
import subprocess
import configparser
import mfcc_Image_classifier as mc

# Load configurations from config file
config = configparser.ConfigParser()
script_dir = os.path.abspath( os.path.dirname( __file__ ) )
ini_path = os.path.join(script_dir,'..\\.config\\config.ini')
config.read(ini_path)

# MQTT settings from config file
BROKER_ADDRESS = config['mqtt']['broker_address']
PORT = int(config['mqtt']['port'])
SUBSCRIBE_TOPIC = config['mqtt']['subscribe_topic']
PUBLISH_TOPIC = config['mqtt']['publish_topic']

# Recording settings from config file
DEVICE = config['recording']['device']
DURATION = config['recording']['duration']
FORMAT = config['recording']['format']
CHANNELS = config['recording']['channels']
RATE = config['recording']['rate']

# Callback when the client receives a CONNACK response from the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(SUBSCRIBE_TOPIC)
        print(f"Subscribed to topic: {SUBSCRIBE_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received from the server
def on_message(client, userdata, message):
    payload = message.payload.decode()
    print(f"Received message '{payload}' on topic '{message.topic}'")
    DURATION=10
    if "#record" in payload.lower():
        s = payload.split(":")
        if len(s)==3:
            DURATION=s[2]
        print("Recording started")

        # Get the current time and create a file with that name
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Recording_{current_time}.wav"
        with open(filename, "w") as f:
            f.write("Recording started at " + current_time)

        print(f"File '{filename}' created")
        
        ############################ RECORDING ################################
        # Execute the record command and wait for it to finish
        
        record_command = f"arecord -D {DEVICE} --duration={DURATION} -f {FORMAT} -c{CHANNELS} -r{RATE} {filename}"
        print("10s recording started...")
        client.publish(PUBLISH_TOPIC, f"{filename} Recording for {DURATION}s started")
        process = subprocess.run(record_command, shell=True, capture_output=True)
        
        # Check if the recording command was successful
        if process.returncode == 0:
            print("Recording command executed successfully")
            client.publish(PUBLISH_TOPIC, f"{filename} Recording Completed")
        else:
            print(f"Recording command failed with error: {process.stderr.decode()}")
            client.publish(PUBLISH_TOPIC, f"{filename} Recording Failed")
            return None
        
        ############################ UPLOADING ################################
        
        client.publish(PUBLISH_TOPIC, f"{filename} file uploading started")
        response = mc.mfcc_generator_github_uploader(filename,s[1])
        
        # Check if the file upload to github is successful
        if response.status_code == 201:
            print("Github upload successfull")
            client.publish(PUBLISH_TOPIC, f"{filename} Upload completed")
        else:
            print(f"Failed to commit file: {response.status_code} - {response.text}")
            client.publish(PUBLISH_TOPIC, f"{filename} file uploading failed")

    elif "#listen" in payload.lower():
        # Get the current time and create a file with that name
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Recording_{current_time}.wav"
        with open(filename, "w") as f:
            f.write("Recording started at " + current_time)

        print(f"File '{filename}' created")
        
        ############################ RECORDING ################################
        # Execute the record command and wait for it to finish
        DURATION=10
        record_command = f"arecord -D {DEVICE} --duration={DURATION} -f {FORMAT} -c{CHANNELS} -r{RATE} {filename}"
        print("10s recording started...")
        client.publish(PUBLISH_TOPIC, f"{filename} Recording for {DURATION}s started")
        process = subprocess.run(record_command, shell=True, capture_output=True)
        
        # Check if the recording command was successful
        if process.returncode == 0:
            print("Recording command executed successfully")
            client.publish(PUBLISH_TOPIC, f"{filename} Recording Completed")
        else:
            print(f"Recording command failed with error: {process.stderr.decode()}")
            client.publish(PUBLISH_TOPIC, f"{filename} Recording Failed")
            return None
        
        ############################ UPLOADING ################################
        
        client.publish(PUBLISH_TOPIC, f"{filename} file uploading started")
        mc.le.classes_ =mc.np.array(['bee', 'cricket', 'noise'])  # Predefined labels
        # Classify the audio segments and get the percentage results
        print("audio_file_path=",filename)
        classification_percentages = mc.classify_audio_segments(filename, mc.model_filename, mc.le)

        print("Classification Percentages:")
        result=""
        for label, percentage in classification_percentages.items():
            print(f"{label}: {percentage:.2f}%")
            result=result+f"{label}: {percentage:.2f}%\n"
        
        client.publish(PUBLISH_TOPIC, f"Result={result}")

# Create MQTT client instance
client = mqtt.Client()

# Attach callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(BROKER_ADDRESS, PORT, 60)

# Blocking loop to process network traffic and dispatch callbacks
client.loop_forever()
