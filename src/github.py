import requests
import base64
import json
import configparser
import os

# Load configurations from config file
config = configparser.ConfigParser()
script_dir = os.path.abspath( os.path.dirname( __file__ ) )
ini_path = os.path.join(script_dir,'..\\.config\\config.ini')
config.read(ini_path)

GITHUB_TOKEN = config['github']['token']
GITHUB_REPO = config['github']['repo']

print("GITHUB_TOKEN",GITHUB_TOKEN)
print("GITHUB_REPO",GITHUB_REPO)
# GitHub API function to commit a file
def commit_file_to_github(mfcc_file_path, github_file_path, commit_message="Committing dataset MFCC file"):
    """
    Function to commit a file to a GitHub repository.
    
    Args:
    - github_file_path (str): The file path in the GitHub repository where the content will be committed.
    - upload_file_path (str): The path of the file to be uploaded to github.
    - commit_message (str): The commit message for the file update. Default is "Committing dataset MFCC file".
    
    Returns:
    - Response: The HTTP response object from the GitHub API.
    """
    # GitHub API settings
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/dataset/{github_file_path}"

    # Encode the content to base64
    with open(mfcc_file_path, "rb") as mfcc_file:
        encoded_content = str(base64.b64encode(mfcc_file.read())).split("'")[1]
    #encoded_content = base64.b64encode(content.encode()).decode()

    # Headers for the HTTP request
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Data payload
    data = {
        "message": commit_message,
        "content": encoded_content
    }

    # Convert the data to a JSON string
    json_data = json.dumps(data)

    # Send the PUT request
    response = requests.put(GITHUB_API_URL, headers=headers, data=json_data)

    return response


def main():
    # Example usage
    github_file_path = "dataset/notes/hello_88.txt"
    upload_file_path = "d:\\Study\\Research\\Sem02_AppliedProject\\GithubRepo\\BioAcousticsMonitoring\\akhil.txt"
    commit_message = "Committing MFCC file"

    # Call the function
    response = commit_file_to_github(github_file_path, upload_file_path, commit_message)

    # Check the response
    if response.status_code == 201:
        print("File committed successfully.")
    else:
        print(f"Failed to commit file: {response.status_code} - {response.text}")

if __name__=="__main__":
    main()