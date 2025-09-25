

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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from streamlit_app import STREAMLIT_APPS
import datetime

options = webdriver.ChromeOptions()
# options.add_argument('--headless=new')  # better JS support
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-gpu')

driver = webdriver.Chrome(options=options)

with open("wakeup_log.txt", "a") as log_file:
    log_file.write(f"Execution started at: {datetime.datetime.now()}\n")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    log_file.write(f"Found iframes: {len(iframes)}")
            
    for url in STREAMLIT_APPS:
        try:
            driver.get(url)
                    
            # dump the HTML to a file
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            # take a screenshot
            driver.save_screenshot("debug_screenshot.png")
            try:
                # wait up to 15s for the button to appear
                button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'get this app back up')]")
                    )
                )
                button.click()
                log_file.write(f"[{datetime.datetime.now()}] Successfully clicked wake-up button at {url}\n")
            except TimeoutException:
                log_file.write(f"[{datetime.datetime.now()}] Wake-up button not found at {url}\n")
        except Exception as e:
            log_file.write(f"[{datetime.datetime.now()}] Error for {url}: {str(e)}\n")

driver.quit()

