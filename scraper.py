try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    driver = webdriver.Chrome()
except:
    print ("AF: No Chrome webdriver installed")
    driver = webdriver.Chrome(ChromeDriverManager().install())

import time
import json
import pandas as pd
import datetime
from tqdm import tqdm
from config import ALLOWED_ELEMENT_TYPES,ICON_COLOR_MAP
from utils import reformat_scraped_data
from webdriver_manager.chrome import ChromeDriverManager

# Start and end dates for 2023
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2023, 12, 31)

# Iterate over each month in 2023
current_date = start_date
while current_date <= end_date:
    driver = webdriver.Chrome() # excepting bot detection
    # Get the first day of the current month
    first_day_of_month = current_date.replace(day=1)
    # Get the last day of the current month
    next_month = first_day_of_month.replace(day=28) + datetime.timedelta(days=4)
    last_day_of_month = next_month - datetime.timedelta(days=next_month.day)
    
    # Format the range
    formatted_range = f"range={first_day_of_month.strftime('%b').lower()}{first_day_of_month.day}.{first_day_of_month.year}-" \
                      f"{last_day_of_month.strftime('%b').lower()}{last_day_of_month.day}.{last_day_of_month.year}"
    
    url = f"https://www.forexfactory.com/calendar?{formatted_range}"
    driver.get(url)
    
    print(url)
    
    
    table = driver.find_element(By.CLASS_NAME, "calendar__table")

    data = []
    previous_row_count = 0
    # Scroll down to the end of the page
    while True:
        # Record the current scroll position
        before_scroll = driver.execute_script("return window.pageYOffset;")

        # Scroll down a fixed amount
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")

        # Wait for a short moment to allow content to load
        time.sleep(0.5)

        # Record the new scroll position
        after_scroll = driver.execute_script("return window.pageYOffset;")

        # If the scroll position hasn't changed, we've reached the end of the page
        if before_scroll == after_scroll:
            break

    # Now that we've scrolled to the end, collect the data
    for row in tqdm(table.find_elements(By.TAG_NAME, "tr")):
        row_data = []
        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute('class')
            if class_name in ALLOWED_ELEMENT_TYPES:
                if element.text:
                    row_data.append(element.text)
                elif "calendar__impact" in class_name:
                    impact_elements = element.find_elements(By.TAG_NAME, "span")
                    for impact in impact_elements:
                        impact_class = impact.get_attribute("class")
                        color = ICON_COLOR_MAP[impact_class]
                    if color:
                        row_data.append(color)
                    else:
                        row_data.append("impact")

        if len(row_data):
            data.append(row_data)
            
    current_utc_time = datetime.datetime.now(datetime.timezone.utc)
    filename = f"{first_day_of_month.strftime('%b').lower()}_{current_utc_time:%Y-%m-%d_%H-%M-%S}_UTC.csv"
    reformat_scraped_data(data,filename)


    # Move to the first day of the next month
    current_date = last_day_of_month + datetime.timedelta(days=1)
    driver.close()