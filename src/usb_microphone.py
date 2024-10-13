import subprocess
from sys import platform

def get_usb_audio_device():
    # Run the 'arecord -l' command and capture the output
    result = subprocess.run(['arecord', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check if there was an error running the command
    if result.returncode != 0:
        print("Error running 'arecord -l':", result.stderr)
        return None, None

    stdout_split= result.stdout.split("\n")
    for line in stdout_split:
        if "usb audio" in line.lower():
            line_split=line.split(":")
            card=line_split[0].split("card ")[1]
            device=line_split[1].split("device ")[1]
            print("card=",card, "device=",device)
            return card, device

    print("No USB Audio device found.")
    return None, None

def record_audio(filename,duration=10):
    card, device =get_usb_audio_device()
    if (card is not None) and (device is not None):
        record_command = f"arecord -D plughw:{card},{device} --duration={duration} -f S16_LE -c2 -r44100 {filename}"
        print("Recording started...")
        process = subprocess.run(record_command, shell=True, capture_output=True)
        if process.returncode == 0:
            return 0, "Recording command executed successfully"
        else:
            print(f"Recording command failed with error: {process.stderr.decode()}")
            return -1, f"{process.stderr.decode()}"
    else:
        return -1,"No USB Audio device found."

        
        
if __name__ == "__main__":
    card_info=get_usb_audio_device()
    print("card_info=",card_info)
    
    result=record_audio("test.wav",2)
    if result[0]==0:
        print(result[1])
    elif result[0]==-1:
        print(result[1])
