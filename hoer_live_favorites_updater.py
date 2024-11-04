from pytube import Playlist
from pytube.innertube import _default_clients
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from threading import Thread, Event
import time
import os
import psutil
import subprocess
import time
import logging
import json

def load_configuration():
    config_file = 'configuration.json'

    default_config = {
        "chrome_path": "",
        "youtube_playlist_url": "",
        "hoer_live_url": "https://hoer.live/",
        "hoer_live_username": "",
        "hoer_live_password": ""
    }

    try:
        # Check if the configuration file exists
        if not os.path.exists(config_file):
            # If the file doesn't exist, create it with default values
            with open(config_file, 'w') as file:
                json.dump(default_config, file, indent=4)
            print_and_log(f"Created new configuration file with default values.")
            return default_config

        # If the file exists, read the configuration
        with open(config_file, 'r') as file:
            config = json.load(file)

        print_and_log(f"Read params from {config_file}.")
        return config
    except Exception as e:
        print(f"Failed to read params from {config_file}: {str(e)}")
        return default_config  # Optionally return default configuration in case of failure

def save_configuration(params, file_name="configuration.json"):
    with open(file_name, "w") as f:
        json.dump(params, f)

def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO,
        force=True)

def print_and_log(text):
    print(text)
    logging.info(text)

def print_and_info(text):
    print("INFO: " + text)
    # Notify the user
    messagebox.showinfo("INFO", text)

def print_and_error(text):
    print("ERROR: " + text)
    # Notify the user
    messagebox.showerror("ERROR", text)

def run_chrome_if_not_running(chrome_path):
    # Chrome debugger command line arguments
    params = [
            chrome_path,
            '--remote-debugging-port=9222',
            '--user-data-dir=' + os.getcwd() + '/ChromeSession',
            '--disable-extensions'
        ]
    # Loop through all running processes
    for process in psutil.process_iter(['name', 'cmdline']):
        try:
            # Check if the app name matches the process name
            if process.info['name'] == "chrome.exe":
                # Check if all specified parameters are in the command line
                if all(param in process.info['cmdline'] for param in params):
                    print_and_log("Browser already started in debug mode...")
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Start the browser in the background without blocking the script
            subprocess.Popen(params)
            print_and_log("Starting browser in debug mode...")
            return
    # Start the browser in the background without blocking the script
    subprocess.Popen(params)
    print_and_log("Starting browser in debug mode...")
    return

def load_website(driver, website_url):
    driver.get(website_url)
    # Wait for the page to load
    time.sleep(1)

# Step 1: Get video titles from YouTube playlist (assuming the get_video_titles function works correctly)
def get_available_video_titles(playlist_url, stop_flag):

    # Sets the default client type for pytube
    _default_clients["ANDROID_MOBILE"] = _default_clients["WEB"]
    
    # Initialize the playlist
    playlist = Playlist(playlist_url)

    setup_logging(playlist.title + ' playlist log.txt')

    print_and_log("Fetching video titles from YouTube playlist...")
    
    # List to store available video titles
    available_videos = []
    
    for video in playlist.videos:
        if stop_flag.is_set():
            return available_videos

        try:
            # Try to access the video's title (this will fail if the video is unavailable)
            title = video.title
            available_videos.append(title)
        except Exception as e:
            # If a video is unavailable, it will throw a KeyError
            print_and_log("A video is unavailable and will be skipped: " + video.title)
            print_and_log(e)
            continue
    
    print_and_log(f"Fetched {len(available_videos)} available video titles.")
    return available_videos

def click_close_popup(driver):
    try:
        popup_close_button = driver.find_element(By.XPATH, '//span[@class="popup__close"]')
        popup_close_button.click()
        print_and_log("Closed popup.")
        time.sleep(1)  # Wait for any transitions or actions to complete
    except Exception as e:
        print_and_log("Popup already closed.")

def click_consent(driver):
    try:
        consent_button = driver.find_element(By.XPATH, '//button[@class="cookie-consent__accept button-white"]')
        consent_button.click()
        print_and_log("Accepted cookies.")
        time.sleep(1)  # Wait for any transitions or actions to complete
    except Exception as e:
        print_and_log("Cookies already accepted.")

def check_if_logged_in(driver, target_website_url):
    try:
        load_website(driver, target_website_url)
    except Exception as e:
        print_and_error("Failed to load website " + target_website_url + "\n\nCheck URL!")
        return False
    
    login_object = driver.find_element(By.XPATH, '//div[@class="hamburger hamburger--slider js-hamburger"]')
    if login_object.is_displayed():
        login_object.click()
        try:
            login_object = driver.find_element(By.XPATH, '//a[text()="Logout"]')
            print_and_log("Logged in.")
            return True
        except Exception as e:
            return False
    else:
        try:
            login_object = driver.find_element(By.XPATH, '//a[@href="/my-account/edit-account/"]')
            print_and_log("Logged in.")
            return True
        except Exception as e:
            return False

def login(username, password, driver, target_website_url):
    try:
        try:
            # Navigate to the website
            print_and_log(f"Navigating to {target_website_url}...")
            load_website(driver, target_website_url)
        except Exception as e:
            print_and_error("Failed to load website " + target_website_url + "\n\nCheck URL!")
            return False

        click_close_popup(driver)
        click_consent(driver)

        print_and_log("Attempting to log in.")

        login_object = driver.find_element(By.XPATH, '//div[@class="hamburger hamburger--slider js-hamburger"]')
        if login_object.is_displayed():
            print_and_log("Logging in through the hamburger element.")
            login_object = driver.find_element(By.XPATH, '//div[@class="hamburger hamburger--slider js-hamburger"]')
            login_object.click()
            time.sleep(1)
            try:
                login_object = driver.find_element(By.XPATH, '//a[text()="Logout"]')
                print_and_log("Already logged in.")
                return True
            except Exception as e:
                login_object = driver.find_element(By.XPATH, '//span[@class="icon icon_member open-popup"]')
                login_object.click()
                time.sleep(1)
        else:
            print_and_log("Logging in through the icon element.")
            try:
                login_object = driver.find_element(By.XPATH, '//a[@href="/my-account/edit-account/"]')
                print_and_log("Already logged in.")
                return True
            except Exception as e:
                login_object = driver.find_element(By.XPATH, '//span[@class="user-letter__text"]')
                login_object.click()
                time.sleep(1)
        login_object = driver.find_element(By.XPATH, '//button[@class="magic-form__next button button_green"]')
        login_object.click()
        login_object = driver.find_element(By.ID, "username")
        login_object.click()
        login_object.send_keys(username)
        login_object = driver.find_element(By.ID, "password")
        login_object.click()
        login_object.send_keys(password)
        login_object = driver.find_element(By.XPATH, '//button[@class="woocommerce-button button woocommerce-form-login__submit"]')
        login_object.click()
        if not check_if_logged_in(driver, target_website_url):
            print_and_error("Failed to togin to " + target_website_url + "\n\nCheck credentials!")
            return False
        return True
    except Exception as e:
        print_and_log(f"Failed to connect to the browser or encountered an error: {e}")
        return False

def toggle_search(driver, title):
    print_and_log(f"Searching for: {title}")
    close_button = driver.find_element(By.XPATH, "//div[@class='search__close toggle-search']")
    if close_button.is_displayed():
        close_button.click()
    search_bar = driver.find_element(By.XPATH, "//span[@class='icon icon_search toggle-search']") 
    search_bar.click()
    search_bar = driver.find_element(By.NAME, "s") 
    search_bar.click()
    search_bar.send_keys(Keys.CONTROL, 'a')
    search_bar.send_keys(Keys.BACKSPACE)
    search_bar.send_keys(title)
    search_bar.send_keys(Keys.RETURN)
    time.sleep(2)  # Wait for the search results to load

def click_result_item(driver):
    # Wait until the element is clickable
    result = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='result no-ajax']")))
    result.click()
    time.sleep(1)

def click_artist_result_item(driver):
    # Wait until the element is clickable
    result = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='result']")))
    result.click()
    time.sleep(1)

def click_label_result_item(driver, split_artist_title_part):
    print_and_log(f"Searching list for: {split_artist_title_part}")
    # Wait until the element is clickable
    result = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='result no-ajax']//span[contains(@class, 'result__title') and contains(text(), '" + split_artist_title_part + "')]")))
    result.click()
    time.sleep(1)

def click_favorite_icon(driver, title):
    try:
        favorite_icon = driver.find_element(By.XPATH, '//div[@class="main-video__icons"]//a[@class="icon icon_heart icon_favorite no-ajax"]')
        favorite_icon.click()
        print_and_log(f"Added to favorites: {title}")
    except Exception as e:
        print_and_log(f"Already favorited: {title}")

def click_artist_favorite_icon(driver, title):
    try:
        favorite_icon = driver.find_element(By.XPATH, '//div[@class="show-card__info"]//a[@class="icon icon_heart icon_favorite no-ajax"]')
        favorite_icon.click()
        print_and_log(f"Added to favorites: {title}")
        time.sleep(1)  # Wait for any transitions or actions to complete
    except Exception as e:
        print_and_log(f"Already favorited: {title}")

# Step 2: Automate browser interaction with Selenium
def automate_website_interaction(chrome_path, available_videos, website_url, username, password, stop_flag):

    run_chrome_if_not_running(chrome_path)

    print_and_log("Starting browser automation...")

    # Connect to an existing Chrome session
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # Ensure this matches the port you used

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print_and_log("Successfully connected to the browser.")

        if stop_flag.is_set():
            return

        if login(username, password, driver, website_url):
            for title in available_videos:
                 # Check for the stop flag regularly
                if stop_flag.is_set():
                    return
                try:
                    # Step 2.1: Search with full video title
                    try:
                        toggle_search(driver, title)
                        click_result_item(driver)
                        click_favorite_icon(driver, title)
                        continue
                    except Exception as e:
                        print_and_log(f"Couldn't find: {title}")

                        if stop_flag.is_set():
                            return
                        # Step 2.2: Search with partial video title
                        try:
                            count_1 = title.count("|")
                            count_2 = title.count("-")
                        
                            if count_1 > 0 and count_2 > 0:
                                print_and_log(f"Retrying attempt 1: using first and last parts of the title...")
                                split_title_part_1 = title.split("|")[0]
                                split_title_part_2 = title.split("-")[-1] # gets tge last part of the string
                                toggle_search(driver, split_title_part_1 + split_title_part_2)
                                click_result_item(driver)
                                click_favorite_icon(driver, title)
                                continue
                            else:
                                print_and_log(f"Retrying attempt 1: using the second half of the title...")
                                split_title_part_2 = title.split("- ")[1] # gets tge last part of the string
                                toggle_search(driver, split_title_part_2)
                                click_result_item(driver)
                                click_favorite_icon(driver, title)
                                continue
                        except Exception as e:
                            if count_1 > 0 and count_2 > 0:
                                print_and_log(f"Couldn't find: {split_title_part_1 + split_title_part_2}")
                            else:
                                print_and_log(f"Couldn't find: {split_title_part_2}")

                            if stop_flag.is_set():
                                return
                            
                            try:
                                if title.index("|") < title.index("-"):
                                    print_and_log(f"Retrying attempt 2: using just the artist name...")
                                    split_title_part_1 = title.split(" |")[0]
                                    toggle_search(driver, split_title_part_1)
                                    click_artist_result_item(driver)
                                    click_artist_favorite_icon(driver, title)
                                else:
                                    print_and_log(f"Retrying attempt 2: using just the label name...")
                                    split_title_label_part = title.split("- ")[0]
                                    toggle_search(driver, split_title_label_part)
                                    split_title_artist_part = title.split("- ")[1].split(" ")[0][0:3]
                                    click_label_result_item(driver, split_title_artist_part)
                                    click_favorite_icon(driver, title)
                                continue
                            except Exception as e:
                                print_and_log(f"Error processing {title}: {e}")
                                continue

                except Exception as e:
                    print_and_log(f"Error processing {title}: {e}")
                    continue

            print_and_log("Browser automation finished.")
        else:
            print_and_log("Failed to log in. Browser automation canceled.")

    except Exception as e:
        print_and_log(f"Failed to connect to the browser or encountered an error: {e}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("hoer.live Favorites Updater")

        # Automation control flags
        self.stop_flag = Event()
        self.automation_thread = None
        self.video_titles = None  # Store the automation result here

        # Set the window size to 800x350 (width x height)
        root.geometry("800x350")
        
        # Create labels and entry boxes for the parameters
        self.chrome_path_label = tk.Label(root, text="chrome.exe Path:")
        self.chrome_path_label.grid(row=0, column=0, padx=5, pady=10, sticky="E")
        self.chrome_path_var = tk.StringVar()
        self.chrome_path_var.trace_add("write", self.on_input_change)
        self.chrome_path_entry = tk.Entry(root, width=100, textvariable=self.chrome_path_var)
        self.chrome_path_entry.grid(row=0, column=1, padx=5, pady=10)
        self.bind_events(self.chrome_path_entry)
        self.submit_button = tk.Button(root, text="Browse", command=lambda: self.file_browse())
        self.submit_button.grid(row=0, column=5, padx=5, pady=10)

        self.youtube_playlist_url_label = tk.Label(root, text="YouTube Playlist URL:")
        self.youtube_playlist_url_label.grid(row=1, column=0, padx=5, pady=10, sticky="E")
        self.youtube_playlist_url_var = tk.StringVar()
        self.youtube_playlist_url_var.trace_add("write", self.on_input_change)
        self.youtube_playlist_url_entry = tk.Entry(root, width=100, textvariable=self.youtube_playlist_url_var)
        self.youtube_playlist_url_entry.grid(row=1, column=1, padx=5, pady=10)
        self.bind_events(self.youtube_playlist_url_entry)

        self.hoer_live_url_label = tk.Label(root, text="hoer.live URL:")
        self.hoer_live_url_label.grid(row=2, column=0, padx=5, pady=10, sticky="E")
        self.hoer_live_url_var = tk.StringVar()
        self.hoer_live_url_var.trace_add("write", self.on_input_change)
        self.hoer_live_url_entry = tk.Entry(root, width=100, textvariable=self.hoer_live_url_var)
        self.hoer_live_url_entry.grid(row=2, column=1, padx=5, pady=10)
        self.bind_events(self.hoer_live_url_entry)

        self.hoer_live_username_label = tk.Label(root, text="hoer.live Username:")
        self.hoer_live_username_label.grid(row=3, column=0, padx=5, pady=10, sticky="E")
        self.hoer_live_username_var = tk.StringVar()
        self.hoer_live_username_var.trace_add("write", self.on_input_change)
        self.hoer_live_username_entry = tk.Entry(root, width=100, textvariable=self.hoer_live_username_var)
        self.hoer_live_username_entry.grid(row=3, column=1, padx=5, pady=10)
        self.bind_events(self.hoer_live_username_entry)

        self.hoer_live_password_label = tk.Label(root, text="hoer.live Password:")
        self.hoer_live_password_label.grid(row=4, column=0, padx=5, pady=10, sticky="E")
        self.hoer_live_password_var = tk.StringVar()
        self.hoer_live_password_var.trace_add("write", self.on_input_change)
        self.hoer_live_password_entry = tk.Entry(root, width=100, textvariable=self.hoer_live_password_var, show="*")  # Using show="*" for password fields
        self.hoer_live_password_entry.grid(row=4, column=1, padx=5, pady=10)
        self.bind_events(self.hoer_live_password_entry)

        # Create buttons
        self.automation_start_button = tk.Button(root, text="Start Automation", command=self.start_automation)
        self.automation_start_button.grid(row=5, column=0, columnspan=1, pady=20)
        self.automation_stop_button = tk.Button(root, text="Stop Automation", command=self.stop_automation, state=tk.DISABLED)
        self.automation_stop_button.grid(row=6, column=0, columnspan=1, pady=20)
        self.configuration_save_button = tk.Button(root, text="Save Configuration", command=self.save)
        self.configuration_save_button.grid(row=5, column=1, columnspan=1, pady=20)
        self.configuration_load_button = tk.Button(root, text="Load Configuration", command=self.load, state=tk.DISABLED)
        self.configuration_load_button.grid(row=6, column=1, columnspan=1, pady=20)

        self.load()

    def file_browse(self):
        file_path = filedialog.askopenfilename(
            title="Select chrome.exe",
            filetypes=(("Executable files", "chrome.exe"), ("All files", "*.*"))
        )
        if file_path:
            self.chrome_path_entry.delete(0, tk.END)
            self.chrome_path_entry.insert(0, file_path)
            self.params["chrome_path"] = file_path

    def run_task_with_result(self):
        # Run the task and store the result in `self.result`
        self.video_titles = get_available_video_titles(self.params["youtube_playlist_url"], self.stop_flag)

    def run_task_without_result(self):
        automate_website_interaction(self.params["chrome_path"], 
                                    self.video_titles, 
                                    self.params["hoer_live_url"], 
                                    self.params["hoer_live_username"], 
                                    self.params["hoer_live_password"], 
                                    self.stop_flag)

        if self.stop_flag.is_set():
            return
        else:    
            self.automation_stop_button.config(state=tk.DISABLED)
            self.automation_start_button.config(state=tk.NORMAL)
            print_and_log("Automation finished.")

    def start_automation(self):
        # Enable stop button, disable start button
        self.automation_stop_button.config(state=tk.NORMAL)
        self.automation_start_button.config(state=tk.DISABLED)

        # Example of a long-running task
        print("Automation started...")

        # Clear the stop flag and start a new automation thread
        self.stop_flag.clear()
        
        try:
            self.automation_thread = Thread(target=self.run_task_with_result)
            self.automation_thread.start()
        except Exception as e:
            print(f"Failed to load YouTube playlist. Error: {e}")
            self.video_titles = None  

        if self.automation_thread is not None:
            self.automation_thread.join()
            if self.video_titles != None:
                self.automation_thread = Thread(target=self.run_task_without_result)
                self.automation_thread.start()
            else:
                print_and_error("Failed to load the YouTube playlist!\n\nCheck playlist permissions or URL!")

    def stop_automation(self):
        print_and_log("Stopping automation...")

        # Set the stop flag to request the thread to stop
        self.stop_flag.set()

        # Disable stop button until automation finishes
        self.automation_stop_button.config(state=tk.DISABLED)

        # Wait for the automation thread to finish
        if self.automation_thread is not None:
            self.automation_thread.join()

        # Re-enable start button after stopping
        self.automation_start_button.config(state=tk.NORMAL)
        print_and_log("Automation stopped.")

    def bind_events(self, entry):
        # Bind events to detect any input change, including paste and mouse actions
        entry.bind("<KeyRelease>", self.on_input_change)
        entry.bind("<ButtonRelease-1>", self.on_input_change)  # Mouse click release
        entry.bind("<FocusOut>", self.on_input_change)

    def on_input_change(self, *args):
        # Disable buttons if any field is empty or if values differ from saved values
        if (self.chrome_path_var.get().strip() == "" or
            self.youtube_playlist_url_var.get().strip() == "" or
            self.hoer_live_url_var.get().strip() == "" or
            self.hoer_live_username_var.get().strip() == "" or
            self.hoer_live_password_var.get().strip() == ""):
            self.automation_start_button.config(state=tk.DISABLED)
            self.configuration_save_button.config(state=tk.DISABLED)
        else:
            if (self.params["chrome_path"] == "" or
                self.params["youtube_playlist_url"] == "" or
                self.params["hoer_live_url"] == "" or
                self.params["hoer_live_username"] == "" or
                self.params["hoer_live_password"] == ""):
                self.automation_start_button.config(state=tk.DISABLED)
                self.configuration_save_button.config(state=tk.NORMAL)
            else:
                if (self.params["chrome_path"] != self.chrome_path_var.get() or
                    self.params["youtube_playlist_url"] != self.youtube_playlist_url_var.get() or
                    self.params["hoer_live_url"] != self.hoer_live_url_var.get() or
                    self.params["hoer_live_username"] != self.hoer_live_username_var.get() or
                    self.params["hoer_live_password"] != self.hoer_live_password_var.get()):
                    self.automation_start_button.config(state=tk.DISABLED)
                    self.configuration_save_button.config(state=tk.NORMAL)
                    self.configuration_load_button.config(state=tk.NORMAL)
                else:
                    self.automation_start_button.config(state=tk.NORMAL)
                    self.configuration_save_button.config(state=tk.DISABLED)
                    self.configuration_load_button.config(state=tk.DISABLED)

    def load(self):
        # Load saved parameters if they exist
        self.params = load_configuration()

        self.chrome_path_var.set(self.params.get("chrome_path", ""))
        self.youtube_playlist_url_var.set(self.params.get("youtube_playlist_url", ""))
        self.hoer_live_url_var.set(self.params.get("hoer_live_url", ""))
        self.hoer_live_username_var.set(self.params.get("hoer_live_username", ""))
        self.hoer_live_password_var.set(self.params.get("hoer_live_password", ""))

    def save(self):
        # Get values from entry field variables
        self.params["chrome_path"] = self.chrome_path_var.get()
        self.params["youtube_playlist_url"] = self.youtube_playlist_url_var.get()
        self.params["hoer_live_url"] = self.hoer_live_url_var.get()
        self.params["hoer_live_username"] = self.hoer_live_username_var.get()
        self.params["hoer_live_password"] = self.hoer_live_password_var.get()

        # Save to JSON file
        save_configuration(self.params)

        self.load()

        print_and_info("Configuration saved successfully!")

# Main function to control steps
def main():
    # Create the application window
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
