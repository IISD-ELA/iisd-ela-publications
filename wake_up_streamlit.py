from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time
from streamlit_app import STREAMLIT_APPS

STREAMLIT_URL = STREAMLIT_APPS[0]

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    with open("wakeup_log.txt", "a") as log_file:
        try:
            driver.get(STREAMLIT_URL)
            print(f"Opened {STREAMLIT_URL}")
            log_file.write(f"Opened {STREAMLIT_URL}")
    
            wait = WebDriverWait(driver, 20)
            try:
                button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes, get this app back up')]"))
                )
                print("Wake-up button found. Clicking with JS...")
                log_file.write("Wake-up button found. Clicking with JS...")
                
                driver.execute_script("arguments[0].click();", button)
    
                # Wait for page reload → look for the app’s root div
                time.sleep(5)
                wait.until(EC.presence_of_element_located((By.ID, "root")))
                print("Page reloaded, app should be waking up...")
                log_file.write("Page reloaded, app should be waking up...")
    
            except TimeoutException:
                print("No wake-up button found. Assuming app already awake.")
                log_file.write("No wake-up button found. Assuming app already awake.")
    
        except Exception as e:
            print(f"Unexpected error: {e}")
            log_file.write(f"Unexpected error: {e}")
            exit(1)
        finally:
            driver.quit()
            print("Script finished.")
            log_file.write("Script finished.")

if __name__ == "__main__":
    main()
