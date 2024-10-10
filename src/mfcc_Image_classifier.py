import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display
import os
import joblib
from PIL import Image
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import github as gt

script_dir = os.path.abspath( os.path.dirname( __file__ ) )
model_filename = os.path.join(script_dir,'..\\samples\\trained_rf_model.pkl')
le = LabelEncoder()
def create_and_save_mfcc(wav_file, output_folder, file_name):
    y, sr = librosa.load(wav_file)
    y = librosa.util.normalize(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=25)

    plt.figure(figsize=(10, 4), dpi=100)
    librosa.display.specshow(mfcc) #, x_axis='time')
    # plt.colorbar()
    # plt.title('MFCC')
    plt.tight_layout()
    
    mfcc_image_path = os.path.join(output_folder, f'MFCC_{file_name}.png')
    plt.savefig(mfcc_image_path)
    plt.close()

# Function to create and save MFCC images from audio segment
def create_mfcc_image(y, sr, file_name):
    y = librosa.util.normalize(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=25)
    plt.figure(figsize=(10, 4),dpi=100)
    librosa.display.specshow(mfcc) #, sr=sr, x_axis='time')
    # plt.colorbar()
    plt.tight_layout()
    
    # Save the MFCC image
    mfcc_image_path = f'{file_name}.png'
    plt.savefig(mfcc_image_path)
    plt.close()
    return mfcc_image_path


# Function to split audio file into 2-second pieces with 1-second overlap
def split_audio(file_path, segment_length=2, overlap=1):
    y, sr = librosa.load(file_path, duration=60)  # Load the 10 second file
    total_segments = []
    step = segment_length - overlap  # Calculate the step for overlapping
    
    for start in np.arange(0, len(y)/sr - segment_length + step, step):
        segment = y[int(start*sr): int((start+segment_length)*sr)]
        total_segments.append((segment, sr))
        # print("total_segments in 10s audio =",start)
    return total_segments

# Function to classify each MFCC image using the pre-trained model
def classify_mfcc_image(image_path, model, label_encoder):
    img = Image.open(image_path)
    img = img.resize((32, 32))
    img_array = np.array(img).flatten().reshape(1, -1)
        
    # Predict the class
    prediction = model.predict(img_array)
    predicted_label = label_encoder.inverse_transform(prediction)
    
    return predicted_label[0]

# Main function to process audio file and classify segments
def classify_audio_segments(file_path, model_filename, label_encoder):
    # Split the audio into 2-second segments
    audio_segments = split_audio(file_path)
    
    label_counts = {label: 0 for label in label_encoder.classes_}
    total_segments = len(audio_segments)
    
    # Load the pre-trained ML model
    model = joblib.load(model_filename)
    
    # Loop over each segment, generate MFCC, classify, and update label counts
    for i, (segment, sr) in enumerate(audio_segments):
        mfcc_image_path = create_mfcc_image(segment, sr, f'mfcc_segment_{i}')
        predicted_label = classify_mfcc_image(mfcc_image_path, model, label_encoder)
        label_counts[predicted_label] += 1
        #print(mfcc_image_path," Prediction=", predicted_label)
        # Clean up (optional: remove the temporary image after classification)
        os.remove(mfcc_image_path)
    
    # Calculate classification percentages
    percentages = {label: (count / total_segments) * 100 for label, count in label_counts.items()}
    
    return percentages

# Main function to process audio file to mfcc and upload to github
def mfcc_generator_github_uploader(audio_file_path, github_dataset_name):
    # Split the audio into 2-second segments
    audio_segments = split_audio(audio_file_path)
          
    # Loop over each segment, generate MFCC, classify, and update label counts
    for i, (segment, sr) in enumerate(audio_segments):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        mfcc_image_path = create_mfcc_image(segment, sr, f'mfcc_{current_time}_{i}')
        response =gt.commit_file_to_github(mfcc_image_path, github_dataset_name+f'/mfcc_test_segment_{i}.png')
        if response.status_code != 201:
            return response
        # Clean up (optional: remove the temporary image after classification)
        os.remove(mfcc_image_path)
    return response
    
# Example usage:
def main():

    audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\Dataset\\BUZZ Dataset\\BUZZ1_FULL\\BUZZ1\\out_of_sample_data_for_validation\\cricket_test\\cricket1_192_168_4_10-2017-08-19_00-00-01.wav"
    # audio_file_path = 'D:\\Study\\Research\\Sem02_AppliedProject\\BeeAudioStorageServer\\Recording_20240906_014847.wav'  # Path to the 10-second .wav audio file
    # audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\Dataset\\BUZZ Dataset\\BUZZ1_Partial_500samples\\BUZZ1\\out_of_sample_data_for_validation\\bee_test\\192_168_4_6-2017-08-09_14-15-01_0.wav"
    audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\Dataset\\BeeAudio_Kaggle\\sound_files\\sound_files\\2022-06-05--17-41-01_2__segment0.wav"
    #audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\Dataset\\ToBeeOrNotToBee_KaggleDataset\\CF003 - Active - Day - (214).wav"
    # audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\BeeAudioStorageServer\\beesoundTest_beeOrNot.wav"
    audio_file_path = "D:\\Study\\Research\\Sem02_AppliedProject\\BeeAudioStorageServer\\beesoundTest_Kaggle.wav"

    mfcc_generator_github_uploader(audio_file_path,"bee_dataset")

    # n = len(sys.argv)
    # print("Number of args=",n)
    # if n>1:
    #     audio_file_path=sys.argv[1]
    
    le.classes_ = np.array(['bee', 'cricket', 'noise'])  # Predefined labels
    # Classify the audio segments and get the percentage results
    print("audio_file_path=",audio_file_path)
    classification_percentages = classify_audio_segments(audio_file_path, model_filename, le)

    print("Classification Percentages:")
    for label, percentage in classification_percentages.items():
        print(f"{label}: {percentage:.2f}%")
        
if __name__=="__main__":
    main()