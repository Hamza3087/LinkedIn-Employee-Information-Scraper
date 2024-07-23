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

# Set up the ChromeDriver path
chrome_driver_path = 'C:\\Users\\dell\\chromedriver-win64\\chromedriver.exe'

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Set up the ChromeDriver service
service = Service(chrome_driver_path)

# Create a new instance of the Chrome driver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function to scroll to the end of the page
def scroll_to_bottom():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Wait for 2 seconds after scrolling

# Function to scroll up the page
def scroll_up():
    driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")

# Function to set search filter to "All"
def set_search_filter_to_all():
    try:
        # Click on the filter dropdown
        filter_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-dropdown__trigger')]"))
        )
        filter_button.click()

        # Select "All" filter
        all_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='All filters']"))
        )
        all_filter.click()

        print("Search filter set to 'All'")
    except Exception as e:
        print(f"Error setting search filter to 'All': {e}")

# Function to extract employee information
def extract_employee_info(location_input, role_input):
    employees = []
    employee_elements = driver.find_elements(By.CSS_SELECTOR, 'li.reusable-search__result-container')
    print(f"Found {len(employee_elements)} employee elements")

    for element in employee_elements:
        try:
            # Check if it's a LinkedIn Member (not in connections)
            is_linkedin_member = element.find_elements(By.CSS_SELECTOR, ".entity-result__title-text a[href*='search/results/people']")
            
            if is_linkedin_member:
                name = "LinkedIn Member"
                profile_url = "N/A"
                connection_degree = "Not connected"
            else:
                name_element = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text a span[aria-hidden='true']")
                name = name_element.text.strip()
                profile_url = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text a").get_attribute('href')
                
                # Extract connection degree
                try:
                    degree_element = element.find_element(By.CSS_SELECTOR, ".entity-result__badge-text")
                    connection_degree = degree_element.text.strip()
                except:
                    connection_degree = "Not connected"

            # Extract subtitle (job title) for both LinkedIn Members and connected profiles
            try:
                subtitle_element = element.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
                full_subtitle = subtitle_element.text.strip()
            except:
                full_subtitle = "N/A"

            # Extract current position from the full subtitle
            current_position = "N/A"
            if "intern @" in full_subtitle.lower():
                current_position = "Intern"
            elif "|" in full_subtitle:
                current_position = full_subtitle.split("|")[-1].strip()

            # Extract location for both LinkedIn Members and connected profiles
            try:
                location = element.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle").text.strip()
            except:
                location = "N/A"

            # Normalize and compare the locations
            role_matches = True if role_input.lower() == 'nill' else role_input.lower() in full_subtitle.lower()
            location_matches = not location_input or location_input.lower() in unidecode(location.lower())
            
            if role_matches and location_matches:
                employees.append({
                    "Name": name,
                    "Full Subtitle": full_subtitle,
                    "Location": location,
                    "Profile URL": profile_url,
                    "Connection Degree": connection_degree
                })
        except Exception as e:
            print(f"Error extracting employee info: {e}")

    return employees

# Function to save employees to a CSV file
def save_to_csv(employees):
    with open('employees.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Name", "Full Subtitle", "Location", "Profile URL", "Connection Degree"])
        writer.writeheader()
        for employee in employees:
            writer.writerow(employee)

try:
    # Take location, role, and company name as input
    while True:
        company_name = input("Enter the company name to search for: ")
        if company_name.strip():
            break
        print("Company name cannot be empty. Please enter a valid company name.")
    
    location_input = input("Enter the location to filter employees by (or leave empty to skip location filtering): ")
    role_input = input("Enter the role to filter employees by (or 'nill' to skip role filtering): ")

    # Navigate to LinkedIn login page
    driver.get('https://www.linkedin.com/login')

    # Set up wait
    wait = WebDriverWait(driver, 40)  # Increased wait time

    # Login
    print("Waiting for username field...")
    username_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
    username_field.send_keys('i210707@nu.edu.pk')
    print("Waiting for password field...")
    password_field = wait.until(EC.presence_of_element_located((By.ID, 'password')))
    password_field.send_keys('Gondal@143')
    print("Waiting for login button...")
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    login_button.click()

    # Wait for the feed page to load
    print("Waiting for global nav...")
    wait.until(EC.presence_of_element_located((By.ID, 'global-nav')))
    print("Login successful!")

    # Locate the search bar in the header
    print("Waiting for search bar...")
    search_bar = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search"]')))
    search_bar.click()
    # Enter the company name and perform the search
    print(f"Entering search term '{company_name}'...")
    search_bar.send_keys(company_name)
    search_bar.send_keys(Keys.ENTER)
    print("Search initiated.")

    # Wait for search results page to load
    print("Waiting for search results...")
    search_results_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
    print("Search results page loaded")

    # Click on the specific company link using CSS selector
    print("Waiting for company link...")
    company_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.app-aware-link')))
    company_link = None
    for link in company_links:
        if company_name.lower() in link.text.lower():
            company_link = link
            break

    if company_link:
        company_link.click()
        print("Company link clicked")
    else:
        print("Company link not found")
        raise Exception("Company link not found in search results")

    # Wait for 5 seconds then scroll up
    time.sleep(5)
    scroll_up()
    print("Scrolled up")

    # Wait for the "51-200 employees" link and click it
    print("Waiting for employees link...")
    employees_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.t-normal.t-black--light.link-without-visited-state.link-without-hover-state')))
    employees_link.click()
    print("Employees link clicked")

    # Set search filter to "All"
    set_search_filter_to_all()

    # Wait for employee results to load
    print("Waiting for employee results...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-results-container')))
    print("Employee results loaded")

    # Wait for specific employee elements to appear
    print("Waiting for employee elements...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.reusable-search__result-container')))
    print("Employee elements found")

    all_employees = []

    try:
        while True:
            # Extract employee information
            print("Extracting employee information...")
            employees = extract_employee_info(location_input, role_input)
            all_employees.extend(employees)

            # Check for the "Next" button and click it if it's not disabled
            try:
                print("Waiting for 5 seconds...")
                time.sleep(5)
                print("Scrolling to the bottom of the page...")
                scroll_to_bottom()
                
                print("Checking for 'Next' button...")
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Next"]'))
                )
                
                if next_button.is_displayed() and not next_button.get_attribute("aria-disabled"):
                    print("Clicking 'Next' button...")
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)  # Wait for the next page to load
                    wait.until(EC.staleness_of(next_button))  # Wait for the 'Next' button to become stale
                else:
                    print("The 'Next' button is either not displayed or disabled. Reached the last page.")
                    break
            except Exception as e:
                print(f"An error occurred while checking/clicking the 'Next' button: {e}")
                break

        if not all_employees:
            print("No employees found. Check the HTML structure.")
        else:
            # Save extracted employee information to CSV
            print("Saving employee information to CSV...")
            save_to_csv(all_employees)
            print("Employee information saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

finally:
        # Close the browser automatically
        print("Closing the browser...")
        driver.quit()

print("Script execution completed.")