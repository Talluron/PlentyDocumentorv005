# PlentyDocumentor
## Plentymarkets Document Downloader


### Overview
Document Downloader is a Python application designed to automate the process of downloading and unzipping documents from Plentymarkets using Plenty's API. 
It features a graphical user interface (GUI) for easy configuration and operation.

### Features
- Login authentication to access document endpoints.
- Fetching document IDs within a specified date range.
- Downloading documents in batches and saving them as ZIP files.
- Unzipping the downloaded documents.
- Configurable parameters through a GUI.
- Option to open the download folder directly from the GUI.

### Prerequisites
Before you begin, ensure you have met the following requirements:
- Python 3.7 or later installed.
- Access to the Plenty API with valid credentials.
- Plenty API User needs *read access to Documents*

#### requirements for python based Version:
- Check requirements.txt file and use with:
  ```bash
  pip install -r requirements.txt
  ```
- or Manual install

### Todo
- Bugfixes
- dynamically generate src file from programm on first start

### Installation

#### Portable:
1. bin/Documentor.zip contains the executable incl. all required files.

#### Everything:
2. Clone the repository:
   ```bash
   git clone https://github.com/Talluron/PlentyDocumentorv005.git
   cd PlentyDocumentorv005
```