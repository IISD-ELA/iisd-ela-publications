from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import os
from streamlit_app import STREAMLIT_APPS

# Streamlit app URL from environment variable (or default)
STREAMLIT_URL = STREAMLIT_APPS[0]

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(STREAMLIT_URL)
        print(f"Opened {STREAMLIT_URL}")

        wait = WebDriverWait(driver, 15)
        try:
            # Look for the wake-up button
            button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes, get this app back up')]"))
            )
            print("Wake-up button found. Clicking...")
            button.click()

            # After clicking, check if it disappears
            try:
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")))
                print("Button clicked and disappeared ✅ (app should be waking up)")
            except TimeoutException:
                print("Button was clicked but did NOT disappear ❌ (possible failure)")
                exit(1)

        except TimeoutException:
            # No button at all → app is assumed to be awake
            print("No wake-up button found. Assuming app is already awake ✅")

    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)
    finally:
        driver.quit()
        print("Script finished.")

if __name__ == "__main__":
    main()


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

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
# from streamlit_app import STREAMLIT_APPS
# import datetime
# import tempfile

# options = webdriver.ChromeOptions()

# # Headless is important on CI
# options.add_argument("--headless=new")   # better than plain --headless
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

# # Force an isolated profile dir
# options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

# # Disable GPU and extensions (can interfere in CI)
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-extensions")

# driver = webdriver.Chrome(options=options)

# with open("wakeup_log.txt", "a") as log_file:
#     log_file.write(f"Execution started at: {datetime.datetime.now()}\n")
            
#     iframes = driver.find_elements(By.TAG_NAME, "iframe")
#     log_file.write(f"(DEBUG 1) Found iframes: {len(iframes)}")
            
#     for url in STREAMLIT_APPS:
#         try:
#             log_file.write(f"Opening {url} ...")
#             driver.get(url)

#             wait_time_s = 30
#             log_file.write(f"Waiting {wait_time_s} seconds for JS to load...")
#             time.sleep(wait_time_s)

#             buttons = driver.find_elements(By.TAG_NAME, "button")
#             log_file.write(f"(DEBUG 2) Found {len(buttons)} buttons:")
#             for i, b in enumerate(buttons, start=1):
#                 log_file.write(f"  Button {i}: '{b.text}'")
                        
#             # dump the HTML to a file
#             with open("debug_page.html", "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
            
#             # take a screenshot
#             driver.save_screenshot("debug_screenshot.png")

#             log_file.write("Saved debug_page.html and debug_screenshot.png")
            
#             try:
#                 # wait up to 30s for the button to appear
#                 button = WebDriverWait(driver, wait_time_s).until(
#                     EC.element_to_be_clickable(
#                         (By.XPATH, "//button[contains(text(), 'get this app back up')]")
#                     )
#                 )
#                 button.click()
#                 log_file.write(f"[{datetime.datetime.now()}] Successfully clicked wake-up button at {url}\n")
#             except TimeoutException:
#                 log_file.write(f"[{datetime.datetime.now()}] Wake-up button not found at {url}\n")
#         except Exception as e:
#             log_file.write(f"[{datetime.datetime.now()}] Error for {url}: {str(e)}\n")

# driver.quit()

