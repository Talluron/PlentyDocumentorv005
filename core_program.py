import json
import os
import zipfile
import requests
from datetime import datetime, timedelta, timezone
import pytz
import dateutil.parser

# Constants
# Inside main()
CONFIG_FILE = "config.txt"
DOWNLOAD_DIR = "./Download"
UNZIP_DIR = f"{DOWNLOAD_DIR}/AllFiles"


# Functions
    

def read_config():
    with open(CONFIG_FILE, 'r') as config_file:
        config = json.load(config_file)
        # Convert dates to simplified format
        for key in ['start_date', 'end_date']:
            if key in config.get('scope', {}):
                iso_date = config['scope'][key]
                simplified_date = dateutil.parser.isoparse(iso_date).strftime('%Y-%m-%d')
                config['scope'][key] = simplified_date
        return config


def save_config(config_data):
    # Convert dates back to ISO format before saving
    for key in ['start_date', 'end_date']:
        if key in config_data.get('scope', {}):
            simplified_date = config_data['scope'][key]
            # Ensure we only have the date part in 'simplified_date'
            if 'T' in simplified_date:
                simplified_date = simplified_date.split('T')[0]
            # Parse the simplified date and convert it back to ISO format
            iso_date = dateutil.parser.parse(simplified_date).isoformat()
            config_data['scope'][key] = iso_date

    if 'bearer_token' in config_data:
        config_data['token_timestamp'] = datetime.now().isoformat()

    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)


def is_token_valid(config):
    if config.get('bearer_token') and 'token_timestamp' in config:
        # Parse the saved timestamp and convert it to a naive datetime object if it's not already
        token_timestamp_str = config['token_timestamp']
        token_timestamp = datetime.fromisoformat(token_timestamp_str)

        # If the saved timestamp is aware, convert it to naive by removing timezone info
        if token_timestamp.tzinfo is not None and token_timestamp.tzinfo.utcoffset(token_timestamp) is not None:
            token_timestamp = token_timestamp.replace(tzinfo=None)

        # Compare with the current naive local time
        return datetime.now() - token_timestamp < timedelta(hours=5)
    return False


def login_and_get_token(login_endpoint):
    # Read the existing config data
    config = read_config()

    if is_token_valid(config):
        print("Using saved token.")
        return config['bearer_token']

    # Extract login credentials
    username = config['login']['username']
    password = config['login']['password']

    # Prepare the payload
    payload = {
        'username': username,
        'password': password
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic Og=="
    }

    # Make the POST request
    response = requests.request("POST", login_endpoint, json=payload, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the token from the response
        token = response.json().get('access_token')
        if token:
            # Save the token to the config file
            config['bearer_token'] = token
            save_config(config)
            print("Token retrieved and saved successfully.")
            return token
        else:
            print("Token not found in the response.")
            return None
    else:
        print(f"Failed to retrieve token. Status code: {response.status_code}")
        return None


def find_document_ids(token, find_doc_endpoint, start_date, end_date):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    params = {
        'createdAtFrom': start_date,
        'createdAtTo': end_date
    }

    document_ids = []
    current_page = 1
    is_last_page = False

    while not is_last_page:
        # Update params to include the current page
        params['page'] = current_page
        
        

        # Make the GET request
        response = requests.get(find_doc_endpoint, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

            # Extract document IDs from the current page
            page_ids = [doc['id'] for doc in data['entries']]
            document_ids.extend(page_ids)
            
            # Check if this is the last page
            is_last_page = data['isLastPage']

            # Increment the page number for the next iteration
            current_page += 1

            #show something
            print("Finding Ids on Page:", current_page, "/", data['lastPageNumber'])

        elif response.status_code == 401:
            # Handle Unauthorized Error
            print("Failed to retrieve document IDs: Unauthorized. Check your credentials & access rights")
            break  # Exit the loop on failure
        else:
            print(f"Failed to retrieve document Ids. Status code: {response.status_code}")
            break  # Exit the loop on failure
        #print("Document IDs to download: ", document_ids)
    return document_ids


def download_documents_as_zip(token, download_zip_endpoint, doc_ids, limits):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    print("Downloading files now...")
    for i in range(0, len(doc_ids), limits):
        batch_ids = doc_ids[i:i + limits]
        filename = f"{i + 1}-{i + len(batch_ids)}.zip"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        payload = {
            "ids": batch_ids,
            "filename": filename
        }
        
        # Make the POST request
        response = requests.get(download_zip_endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            # Save the ZIP file
            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"Batch {i // limits + 1}: Saved {filename}")
        else:
            print(f"Failed to download documents. Status code: {response.status_code}")
            print(response.text)  # This will help in debugging


def unzip_files():
    
    if not os.path.exists(UNZIP_DIR):
        os.makedirs(UNZIP_DIR)
    print("Unzipping to", os.path.abspath(UNZIP_DIR))
    
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith('.zip'):
            zip_filepath = os.path.join(DOWNLOAD_DIR, filename)
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                # Extract all the contents of the zip file into UNZIP_DIR
                zip_ref.extractall(UNZIP_DIR)
            print(f"Unzipped {filename}")


# Main process
def main():
    # Read config
    config = read_config()

    # Define endpoints using the URL from the config
    PLENTY_URL = config['plenty_url']
    LOGIN_ENDPOINT = f"{PLENTY_URL}/rest/login"
    FIND_DOC_ENDPOINT = f"{PLENTY_URL}/rest/orders/documents/find"
    DOWNLOAD_ZIP_ENDPOINT = f"{PLENTY_URL}/rest/orders/documents/downloads/as_zip"
    # print(LOGIN_ENDPOINT)

    # Step 1: Login and retrieve token
    token = login_and_get_token(LOGIN_ENDPOINT)

    # Step 2: Find document IDs
    simplified_start_date = config['scope']['start_date']
    simplified_end_date = config['scope']['end_date']

    # Define the timezone
    cet = pytz.timezone('Europe/Berlin')   #TODO Time Zone selector in GUI
    
    # Convert the simplified dates to ISO format with time and timezone
    start_date = cet.localize(datetime.strptime(simplified_start_date, '%Y-%m-%d')).isoformat()
    end_date = cet.localize(datetime.strptime(simplified_end_date, '%Y-%m-%d')).isoformat()

    doc_ids = find_document_ids(token, FIND_DOC_ENDPOINT, start_date, end_date)

    # Step 3: Download documents as ZIP
    limits = config['scope']['batch_size']
    download_documents_as_zip(token, DOWNLOAD_ZIP_ENDPOINT, doc_ids, limits)

    # Step 4: Unzip files
    unzip_files()


if __name__ == "__main__":
    main()
