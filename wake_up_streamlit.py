

#========================================METHOD#1==============================================================
# import requests
# import datetime
# from streamlit_app import STREAMLIT_APPS

# with open("wakeup_log.txt", "a", encoding="utf-8") as log_file:
#     log_file.write(f"Execution started at: {datetime.datetime.now()}\n")

#     for url in STREAMLIT_APPS:
#         try:
#             r = requests.get(url, timeout=30)
#             content = r.text.lower()
#             log_file.write(f"Retrieved contents via GET API: \n{content}\n")
#             if r.status_code == 200:
#                 if "get this app back up" in content or "app is sleeping" in content:
#                     log_file.write(f"[{datetime.datetime.now()}] App was asleep at: {url} → ping sent to wake it\n")
#                 else:
#                     log_file.write(f"[{datetime.datetime.now()}] App already awake at: {url}\n")
#             else:
#                 log_file.write(f"[{datetime.datetime.now()}] Unexpected status {r.status_code} for {url}\n")

#         except Exception as e:
#             log_file.write(f"[{datetime.datetime.now()}] Error pinging {url}: {str(e)}\n")


#================================METHOD#2==============================================================
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException
# from streamlit_app import STREAMLIT_APPS
# import datetime

# # Set up Selenium webdriver
# options = webdriver.ChromeOptions()
# options.add_argument('--headless')
# driver = webdriver.Chrome(options=options)

# # Initialize log file
# with open("wakeup_log.txt", "a") as log_file:
#     log_file.write(f"Execution started at: {datetime.datetime.now()}\n")

#     # Iterate through each URL in the list
#     for url in STREAMLIT_APPS:
#         try:
#             # Navigate to the webpage
#             driver.get(url)
            
#             # Wait for the page to load
#             WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

#             # Check if the wake up button exists
#             try:
#                 button = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.XPATH, "//button[text()='Yes, get this app back up!']"))
#                 )
#                 button.click()
#                 log_file.write(f"[{datetime.datetime.now()}] Successfully woke up app at: {url}\n")
#             except TimeoutException:
#                 log_file.write(f"[{datetime.datetime.now()}] Button not found for app at: {url}\n")
        
#         except Exception as e:
#             log_file.write(f"[{datetime.datetime.now()}] Error for app at {url}: {str(e)}\n")

# # Close the browser
# driver.quit()

#===============================================METHOD#3===========================================

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from streamlit_app import STREAMLIT_APPS
import datetime
import time

# Set up headless Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')  # use the new headless mode for JS support
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=options)

with open("wakeup_log.txt", "a") as log_file:
    log_file.write(f"Execution started at: {datetime.datetime.now()}\n")
    
    for url in STREAMLIT_APPS:
        try:
            driver.get(url)  # just visit the page
            time.sleep(5)    # wait a few seconds to let JS trigger the wake-up
            log_file.write(f"[{datetime.datetime.now()}] Pinged app at: {url} to wake it\n")
        except Exception as e:
            log_file.write(f"[{datetime.datetime.now()}] Error pinging {url}: {str(e)}\n")

driver.quit()

