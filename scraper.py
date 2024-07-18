# from selenium import webdriver
import undetected_chromedriver as uc
driver = uc.Chrome()

import time
import datetime
from tqdm import tqdm
from utils import reformat_scraped_data
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag

# Start and end dates for 2023
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2023, 12, 31)
latest_time = ''

# Set timezone
driver.get('https://www.forexfactory.com/')
wait = WebDriverWait(driver, 10)
a_tag = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@href="/timezone"]')))
a_tag.click()
timezone_select = wait.until(EC.element_to_be_clickable((By.ID, "time_zone_modal")))
for option in timezone_select.find_elements(By.TAG_NAME, "option"):
    if option.get_attribute("value") == "Etc/UTC":
        option.click()
        break
    
time_format_select = wait.until(EC.element_to_be_clickable((By.ID, "time_format_modal")))
for option in time_format_select.find_elements(By.TAG_NAME, "option"):
    if option.get_attribute("value") == "0":
        option.click()
        break
    
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Save Settings']")))
submit_button.click()

################

# get numerical value to calc better/worse flag
def tag_num_value(tag_txt:str):
    if isinstance(tag_txt, Tag): tag_txt = tag_txt.text
    try:
        return float(tag_txt.rstrip('KBMT%'))
    except:
        return float('nan')

# Iterate over each month in 2023
current_date = start_date
while current_date <= end_date:
    # Get the first day of the current month
    first_day_of_month = current_date.replace(day=1)
    # Get the last day of the current month
    next_month = first_day_of_month.replace(day=28) + datetime.timedelta(days=4)
    last_day_of_month = next_month - datetime.timedelta(days=next_month.day)
    
    # Format the range
    formatted_range = f"range={first_day_of_month.strftime('%b').lower()}{first_day_of_month.day}.{first_day_of_month.year}-" \
                      f"{last_day_of_month.strftime('%b').lower()}{last_day_of_month.day}.{last_day_of_month.year}"
    
    url = f"https://www.forexfactory.com/calendar?{formatted_range}"
    time.sleep(0.5)
    driver.get(url)
    print(url)
    data = []
    previous_row_count = 0
    # Scroll down to the end of the page
    while True:
        before_scroll = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 300);")
        time.sleep(0.25)
        after_scroll = driver.execute_script("return window.pageYOffset;")
        # If the scroll position hasn't changed, we've reached the end of the page
        if before_scroll == after_scroll:
            break
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find('table', class_ = "calendar__table")
    
    # Now that we've scrolled to the end, collect the data
    # "Date", "Time", "Currency", "Impact", "Description", "Actual", "Forecast", "Previous", "Revised from", "FF event ID#", "Group ID#", "Actual better/worse", "Revised from better/worse"
    for subtable in tqdm(table.findChildren("tbody")):
        date_tag = subtable.find('tr', class_='calendar__row')
        date = date_tag.find('span').text
        date_tag.extract()
        for row in subtable.findChildren('tr'):
            try:
                prev_tag:Tag = row.find("td", class_= "calendar__previous").find('span')
            except:
                continue
            revised_from = ''
            if prev_tag.get('class') and 'revised' in prev_tag.get('class'):
                revised_from = prev_tag['title'].split()[-1]
                
            actual = row.find("td", class_= "calendar__actual").find('span')
            forecast = row.find("td", class_= "calendar__forecast").find('span')
            currency = row.find("td", class_= "calendar__currency").find('span')
            desc = row.find("td", class_= "calendar__event").find('span')
            time_ = row.find("td", class_= "calendar__time")
            if len(time_.text.strip()): latest_time = time_.text.strip()
            
            data.append({
                "Date": date,
                "Time": latest_time,
                "Currency": currency.text if currency else '',
                "Impact": row.find("td", class_= "calendar__impact").find('span')['title'][0],
                "Description": desc.text if desc else '',
                "Actual": actual.text if actual else '',
                "Forecast": forecast.text if forecast else '',
                "Previous": prev_tag.text,
                "Revised from": revised_from,
                "FF event ID": row['data-event-id'],
                "Actual better/worse": (1 if tag_num_value(actual) > tag_num_value(prev_tag) else 2 if tag_num_value(actual) < tag_num_value(prev_tag) else 0) if actual and prev_tag else 0,
                "Revised from better/worse": (1 if tag_num_value(actual) < tag_num_value(revised_from) else 2 if tag_num_value(actual) > tag_num_value(revised_from) else 0) if actual and revised_from else 0
            })
            
    current_utc_time = datetime.datetime.now(datetime.timezone.utc)
    filename = f"{first_day_of_month.strftime('%b').lower()}_{current_utc_time:%Y-%m-%d_%H-%M-%S}_UTC.csv"
    reformat_scraped_data(data,filename)

    current_date = last_day_of_month + datetime.timedelta(days=1)
    
driver.close()