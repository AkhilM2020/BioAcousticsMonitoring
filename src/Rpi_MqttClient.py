import paho.mqtt.client as mqtt
import os
import mfcc_Image_classifier as mc
import usb_microphone as um
from sys import platform
import configparser

# Load configurations from config file
config = configparser.ConfigParser()
script_dir = os.path.abspath( os.path.dirname( __file__ ) )
if 'linux' in platform:
    ini_path = os.path.join(script_dir,'../.config/config.ini')
elif 'win' in platform:
    ini_path = os.path.join(script_dir,'..\\.config\\config.ini')
config.read(ini_path)

# MQTT settings from config file
BROKER_ADDRESS = config['mqtt']['broker_address']
PORT = int(config['mqtt']['port'])
SUBSCRIBE_TOPIC = config['mqtt']['subscribe_topic']
PUBLISH_TOPIC = config['mqtt']['publish_topic']

# Machine Learning model settings from config file
CLASS_LABELS = config['machine_learning']['class_lables']

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
    DURATION=10 # default duration in seconds
    
   
    if "#record" in payload.lower(): #Command format : #record:<dataset label>:<duration>
        command_received = payload.split(":")
        if len(command_received)==3:
            DURATION=command_received[2]
        print("Recording started")
        
        ############################ RECORDING ################################
        # Execute the record command and wait for it to finish
        wav_filename = f"Sound_Recording.wav"
        client.publish(PUBLISH_TOPIC, f"Starting audio capturing for {DURATION}s")
        result=um.record_audio(wav_filename,DURATION)
        if result[0]==0:
            print(result[1])
            client.publish(PUBLISH_TOPIC, f"Successfully captured audio for {DURATION}s")
        elif result[0]==-1:
            print(f"Audio capturing failed with error: {result[1]}")
            client.publish(PUBLISH_TOPIC, f"Audio capturing failed with error: {result[1]}")
            return None         
        
        ############################ UPLOADING ################################
        
        client.publish(PUBLISH_TOPIC, f"Starting to upload files to Github")
        response = mc.mfcc_generator_github_uploader(wav_filename,command_received[1],DURATION)
        
        # Check if the file upload to github is successful
        if response.status_code == 201:
            print("Github upload successfull")
            client.publish(PUBLISH_TOPIC, f"MFCC Dataset upload to Github completed")
        else:
            print(f"Failed to commit file to Github: {response.status_code} - {response.text}")
            client.publish(PUBLISH_TOPIC, f"MFCC file uploading to Github failed: {response.status_code} - {response.text}")

    elif "#listen" in payload.lower():
       
        ############################ LISTENING ################################
        # Execute the record command and wait for it to finish
        
        DURATION=10  #default duration in seconds
        model_filename=mc.model_filename #default model file name
        
        command_received = payload.split(":")
        if len(command_received)==2:
            DURATION=command_received[1]
        elif len(command_received)==3:
            DURATION=command_received[1]
            model_filename=command_received[2]
        
        wav_filename = f"Sound_Recording.wav"
        client.publish(PUBLISH_TOPIC, f"Starting audio listening for {DURATION}s")
        result=um.record_audio(wav_filename,DURATION)
        if result[0]==0:
            print(result[1])
            client.publish(PUBLISH_TOPIC, f"Successfully listened for {DURATION}s")
        elif result[0]==-1:
            print(f"Audio listening failed with error: {result[1]}")
            client.publish(PUBLISH_TOPIC, f"Audio listening failed with error: {result[1]}")
            return None         
        
        ############################ CLASSIFYING ################################
        
        mc.le.classes_ =mc.np.array(CLASS_LABELS.split(','))  # Predefined labels
        # Classify the audio segments and get the percentage results
        client.publish(PUBLISH_TOPIC, f"Starting audio classification using {model_filename} model")
        classification_percentages = mc.classify_audio_segments(wav_filename, DURATION, model_filename, mc.le)

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
