import json
import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox, Label, Entry, ttk
from tkcalendar import DateEntry
import datetime
from datetime import timedelta
import dateutil.parser
import core_program  # Import your core program
from core_program import save_config
import threading

CONFIG_FILE = "config.txt"
CONFIG_TEMPLATE = "./src/_onf.jso_" # Copy Source for the Config.txt
DOWNLOAD_DIR = "./Download"

# Functions


def load_config():
    if not os.path.isfile(CONFIG_FILE):
        try:
            shutil.copy(CONFIG_TEMPLATE, CONFIG_FILE)
            print(f"Created {CONFIG_FILE} from template.")
        except Exception as e:
            print(f"Failed to create {CONFIG_FILE} from template: {str(e)}")
            return {}

    try:
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            # Convert dates to simplified format
            for key in ['start_date', 'end_date']:
                if key in config.get('scope', {}):
                    iso_date = config['scope'][key]
                    simplified_date = dateutil.parser.isoparse(iso_date).strftime('%Y-%m-%d')
                    config['scope'][key] = simplified_date
            return config
    except Exception as e:
        print(f"Failed to read {CONFIG_FILE}: {str(e)}")
        return {}


def open_download_folder():
    folder_path = os.path.abspath(DOWNLOAD_DIR)  # Get absolute path of the download directory
    try:
        # Open the folder in the default file explorer
        if os.name == 'nt':  # for Windows
            os.startfile(folder_path)
        elif os.name == 'posix':  # for macOS, Linux
            subprocess.Popen(['open', folder_path])
        else:
            # Just in case an OS is not covered above
            subprocess.Popen(['xdg-open', folder_path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open folder: {str(e)}")


def get_formatted_date(date):
    # Format the date as "YYYY-MM-DDT00:00:01+00:00"
    return date.strftime('%Y-%m-%dT00:00:01+00:00')

class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, str):
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)  # Auto-scroll to the end

    def flush(self):
        pass

# Initialize the main window
root = tk.Tk()
root.title("Documentor - Document Downloader for Plenty - v002")

# Load configuration from the file
config = load_config()
paddx = 10
paddy = 10

# URL
url_label = Label(root, text="URL: ")
url_label.grid(row=0, column=0, sticky="E", padx=paddx, pady=paddy)
url_entry = Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=paddx, pady=paddy)
url_entry.insert(0, config.get('plenty_url', ''))  # Default to empty string if not found

# Login - Username
username_label = Label(root, text="Username: ")
username_label.grid(row=1, column=0, sticky="E", padx=paddx, pady=paddy)
username_entry = Entry(root, width=50)
username_entry.grid(row=1, column=1, padx=paddx, pady=paddy)
username_entry.insert(0, config.get('login', {}).get('username', ''))

# Login - PW
password_label = Label(root, text="Password: ")
password_label.grid(row=2, column=0, sticky="E", padx=paddx, pady=paddy)
password_entry = Entry(root, width=50, show="*")
password_entry.grid(row=2, column=1, padx=paddx, pady=paddy)
password_entry.insert(0, config.get('login', {}).get('password', ''))

# Scope - Start Date
start_date_label = Label(root, text="Start Date: ")
start_date_label.grid(row=3, column=0, sticky="E", padx=paddx, pady=paddy)
start_date_entry = DateEntry(root, width=47, year=datetime.datetime.now().year, 
                             date_pattern='y-mm-dd', selectmode='day')
start_date_entry.grid(row=3, column=1, padx=paddx, pady=paddy)
start_date_entry.set_date(config.get('scope', {}).get('start_date', datetime.datetime.now()))

# Scope - End Date
end_date_label = Label(root, text="End Date: ")
end_date_label.grid(row=4, column=0, sticky="E", padx=paddx, pady=paddy)
end_date_entry = DateEntry(root, width=47, year=datetime.datetime.now().year, 
                           date_pattern='y-mm-dd', selectmode='day')
end_date_entry.grid(row=4, column=1, padx=paddx, pady=paddy)
end_date_entry.set_date(config.get('scope', {}).get('end_date', datetime.datetime.now()))


end_date_label2 = Label(root, text="25. bis 25. = 25. bis 26. 0 Uhr")
end_date_label2.grid(row=4, column=2, sticky="E", padx=paddx, pady=paddy)

# Scope - Batch Size
batch_size_label = Label(root, text="Batch Size: ")
batch_size_label.grid(row=5, column=0, sticky="E", padx=paddx, pady=paddy)
batch_size_entry = Entry(root, width=50)
batch_size_entry.grid(row=5, column=1, padx=paddx, pady=paddy)
batch_size_entry.insert(0, config.get('scope', {}).get('batch_size', ''))

# Button to open dl folder
open_folder_button = tk.Button(root, text="Open Download Folder", command=open_download_folder)
open_folder_button.grid(row=7, column=0, sticky="E", padx=paddx, pady=paddy)

cli_output_label = tk.Label(root, text="CLI Output:")
cli_output_label.grid(row=8, column=0, padx=paddx, pady=paddy, columnspan=2, sticky="W")

cli_output_text = tk.Text(root, height=10, width=80)
cli_output_text.grid(row=9, column=0, columnspan=3, padx=paddx, pady=paddy)

# Scrollbar for Text Widget
scrollb = tk.Scrollbar(root, command=cli_output_text.yview)
scrollb.grid(row=9, column=3, sticky='nsew')
cli_output_text['yscrollcommand'] = scrollb.set

# Function for main program


def update_values_from_inp():
    # Update config with values from the input fields
    config['scope']['start_date'] = get_formatted_date(start_date_entry.get_date())
    end_date = end_date_entry.get_date() + timedelta(days=1)
    config['scope']['end_date'] = get_formatted_date(end_date)

    config['plenty_url'] = url_entry.get()
    config['login'] = {
        'username': username_entry.get(),
        'password': password_entry.get()
    }
    config['scope']['batch_size'] = int(batch_size_entry.get())
    


def run_program():
    
    def task():
        # Start the progress bar
        progress_bar.start(5)  # The number inside start() is the speed of the progress bar
        

        # Save updated config
        
        save_config(config)

        # Redirect stdout to the Text widget
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(cli_output_text)

        try:
            # Run the main program from core_program
            core_program.main()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run the program: {str(e)}")
        finally:
            sys.stdout = old_stdout  # Reset stdout

        # Done
        progress_bar.stop()
        messagebox.showinfo("Info", "Program Done!")
        root.after(0, lambda: status_label.config(text="Completed"))
    # Create and start a thread to run the task
    threading.Thread(target=task).start()


def save_programm():
    # Update config with values from the input fields
    update_values_from_inp()
    
    # Save updated config
    save_config(config)
    messagebox.showinfo("Info", "Saved")


# Save btn
run_button = tk.Button(root, text="Save Config", command=save_programm)
run_button.grid(row=7, column=1, sticky="E", padx=paddx, pady=paddy)


# Run btn
run_button = tk.Button(root, text=" Run Program", command=run_program)
run_button.grid(row=7, column=2, sticky="E", padx=paddx, pady=paddy)

#progress
progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='indeterminate')
progress_bar.grid(row=11, column=0, columnspan=3, padx=paddx, pady=paddy, sticky="EW")

root.mainloop()
