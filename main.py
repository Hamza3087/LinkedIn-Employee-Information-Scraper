from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import csv
from unidecode import unidecode
import asyncio
import io
import uvicorn
from uuid import uuid4

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow requests from any origin
    allow_credentials=True,       # Allow cookies and other credentials in requests
    allow_methods=["*"],          # Allow all HTTP methods in requests
    allow_headers=["*"],          # Allow all headers in requests
)


# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up the ChromeDriver path
chrome_driver_path = 'C:\\Users\\dell\\chromedriver-win64\\chromedriver.exe'

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Set up the ChromeDriver service
service = Service(chrome_driver_path)

class SearchInput(BaseModel):
    company_name: str
    location_input: Optional[str] = None
    role_input: Optional[str] = None
    linkedin_email: str
    linkedin_password: str

class SearchResult:
    def __init__(self, filename: str, status: str = "pending"):
        self.filename = filename
        self.status = status
        self.buffer = io.StringIO()

search_results = {}

def create_driver():
    return webdriver.Chrome(service=service, options=chrome_options)

def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def scroll_up(driver):
    driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")

def set_search_filter_to_all(driver):
    try:
        filter_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-dropdown__trigger')]"))
        )
        filter_button.click()

        all_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='All filters']"))
        )
        all_filter.click()

        print("Search filter set to 'All'")
    except Exception as e:
        print(f"Error setting search filter to 'All': {e}")

def extract_employee_info(driver, location_input, role_input):
    employees = []
    employee_elements = driver.find_elements(By.CSS_SELECTOR, 'li.reusable-search__result-container')
    print(f"Found {len(employee_elements)} employee elements")

    for element in employee_elements:
        try:
            is_linkedin_member = element.find_elements(By.CSS_SELECTOR, ".entity-result__title-text a[href*='search/results/people']")
            
            if is_linkedin_member:
                name = "LinkedIn Member"
                profile_url = "N/A"
            else:
                name_element = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text a span[aria-hidden='true']")
                name = name_element.text.strip()
                profile_url = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text a").get_attribute('href')
                
            try:
                subtitle_element = element.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
                full_subtitle = subtitle_element.text.strip()
            except:
                full_subtitle = "N/A"

            current_position = "N/A"
            if "intern @" in full_subtitle.lower():
                current_position = "Intern"
            elif "|" in full_subtitle:
                current_position = full_subtitle.split("|")[-1].strip()

            try:
                location = element.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle").text.strip()
            except:
                location = "N/A"

            role_matches = True if role_input.lower() == 'nill' else role_input.lower() in full_subtitle.lower()
            location_matches = not location_input or location_input.lower() in unidecode(location.lower())
            
            if role_matches and location_matches:
                employees.append({
                    "Name": name,
                    "Full Subtitle": full_subtitle,
                    "Location": location,
                    "Profile URL": profile_url
                })
        except Exception as e:
            print(f"Error extracting employee info: {e}")

    return employees

async def run_selenium(search_id: str, company_name: str, location_input: Optional[str], role_input: Optional[str], linkedin_email: str, linkedin_password: str):
    driver = create_driver()
    all_employees = []
    try:
        driver.get('https://www.linkedin.com/login')
        wait = WebDriverWait(driver, 40)

        username_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        username_field.send_keys(linkedin_email)
        password_field = wait.until(EC.presence_of_element_located((By.ID, 'password')))
        password_field.send_keys(linkedin_password)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button.click()

        wait.until(EC.presence_of_element_located((By.ID, 'global-nav')))

        search_bar = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search"]')))
        search_bar.click()
        search_bar.send_keys(company_name)
        search_bar.send_keys(Keys.ENTER)

        search_results_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))

        company_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.app-aware-link')))
        company_link = None
        for link in company_links:
            if company_name.lower() in link.text.lower():
                company_link = link
                break

        if company_link:
            company_link.click()
        else:
            raise Exception("Company link not found in search results")

        time.sleep(5)
        scroll_up(driver)

        employees_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.t-normal.t-black--light.link-without-visited-state.link-without-hover-state')))
        employees_link.click()

        set_search_filter_to_all(driver)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-results-container')))

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.reusable-search__result-container')))

        while True:
            employees = extract_employee_info(driver, location_input, role_input)
            all_employees.extend(employees)

            try:
                time.sleep(5)
                scroll_to_bottom(driver)
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Next"]'))
                )

                if next_button.is_displayed() and not next_button.get_attribute("aria-disabled"):
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)
                    wait.until(EC.staleness_of(next_button))
                else:
                    break
            except Exception as e:
                print(f"An error occurred while checking/clicking the 'Next' button: {e}")
                break

        if not all_employees:
            print("No employees found. Check the HTML structure.")
        else:
            print("Employee Info Found")

        search_results[search_id].status = "completed"
        save_to_csv(all_employees, search_id, company_name, role_input, location_input)
    except Exception as e:
        search_results[search_id].status = "failed"
        print(f"Error in run_selenium: {str(e)}")
    finally:
        driver.quit()

def save_to_csv(employees, search_id, company_name, role_input, location_input):
    result = search_results[search_id]
    writer = csv.DictWriter(result.buffer, fieldnames=["Name", "Full Subtitle", "Location", "Profile URL"])
    writer.writeheader()
    for employee in employees:
        writer.writerow(employee)
    result.buffer.seek(0)
    
    # Sanitize company name, role, and location for filename
    sanitized_company_name = ''.join(c for c in company_name if c.isalnum() or c.isspace()).replace(" ", "_").lower()
    filename_parts = [f"employee_list_{sanitized_company_name}"]
    
    if role_input:
        sanitized_role = ''.join(c for c in role_input if c.isalnum() or c.isspace()).replace(" ", "_").lower()
        filename_parts.append(sanitized_role)
    
    if location_input:
        sanitized_location = ''.join(c for c in location_input if c.isalnum() or c.isspace()).replace(" ", "_").lower()
        filename_parts.append(sanitized_location)
    
    result.filename = f"{'-'.join(filename_parts)}.csv"

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/search_employees")
async def search_employees(search_input: SearchInput, background_tasks: BackgroundTasks):
    search_id = str(uuid4())
    filename = f"{search_id}.csv"
    search_results[search_id] = SearchResult(filename)
    
    background_tasks.add_task(run_selenium, search_id, search_input.company_name, search_input.location_input, 
                              search_input.role_input, search_input.linkedin_email, search_input.linkedin_password)
    
    return {"message": "Search started", "search_id": search_id}

@app.get("/search_status/{search_id}")
async def get_search_status(search_id: str):
    if search_id not in search_results:
        raise HTTPException(status_code=404, detail="Search not found")
    return {"status": search_results[search_id].status}

@app.get("/download_csv/{search_id}")
async def download_csv(search_id: str):
    if search_id not in search_results:
        raise HTTPException(status_code=404, detail="File not found")
    
    result = search_results[search_id]
    if result.status != "completed":
        raise HTTPException(status_code=400, detail="File not ready for download")
    
    result.buffer.seek(0)
    return StreamingResponse(
        result.buffer, 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={result.filename}"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)