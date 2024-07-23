
# LinkedIn Employee Information Scraper
This script automates the process of extracting employee information from LinkedIn based on a
specified company name, location, and role. The extracted data is saved into a CSV file.
Prerequisites
1. Python 3.x installed on your machine.
2. Google Chrome browser installed.
3. ChromeDriver compatible with your version of Chrome. Download from here and place
it in the specified directory (file location to be updated in code).
Required Libraries
Before running the script, you need to install the following Python libraries:
1. selenium
2. csv
You can install them using pip:
o pip install selenium
o pip install pandas
How to Run the Program
1. Download the Script
Save the provided Python script to a file, for example, linkedin_scraper.py.
2. Run the Script
Open a terminal or command prompt and navigate to the directory where you saved the
script. Run the script using Python:
o python linkedin_scraper.py
 Provide Inputs
When prompted, enter the following inputs:
 Company Name: The name of the company you want to search for on LinkedIn.
 Location (optional): The location to filter employees by. Leave empty to skip location
filtering.
 Role (optional): The role to filter employees by. Enter 'nill' to skip role filtering.
 Wait for the Script to Complete
The script will navigate LinkedIn, perform the search, and extract employee information. The
extracted data will be saved to a file named employees.csv in the same directory as the script.
Script Explanation
Imports
 selenium.webdriver for controlling the Chrome browser.
 selenium.webdriver.common.by.By for element locating strategies.
 selenium.webdriver.chrome.service.Service for managing the ChromeDriver service.
 selenium.webdriver.chrome.options.Options for setting Chrome options.
 selenium.webdriver.support.ui.WebDriverWait for explicit waits.
 selenium.webdriver.support.expected_conditions as EC for expected conditions in
waits.
 selenium.webdriver.common.keys.Keys for keyboard interactions.
 time for sleep intervals.
 csv for writing to CSV files.
Functions
 scroll_to_bottom(): Scrolls to the bottom of the page.
 scroll_up(): Scrolls up the page.
 set_search_filter_to_all(): Sets the search filter to "All".
 extract_employee_info(location_input, role_input): Extracts employee information from the
search results.
 save_to_csv(employees): Saves the extracted employee information to a CSV file.
Main Execution Flow
1. Set Up ChromeDriver and Browser Options: Initialize the ChromeDriver with specified options.
2. Take User Inputs: Prompt the user for company name, location, and role.
3. Log In to LinkedIn: Navigate to LinkedIn login page and log in using predefined credentials.
4. Perform Company Search: Use the search bar to find the specified company and navigate to its
profile.
5. Extract Employee Information: Iterate through the employee list, extracting and saving the
relevant information.
6. Save Data to CSV: Write the extracted employee information to employees.csv.
7. Close Browser: Wait for user input to close the browser
