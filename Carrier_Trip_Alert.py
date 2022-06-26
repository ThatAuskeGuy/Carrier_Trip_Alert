from configparser import ConfigParser
from datetime import datetime, timedelta
import random
import time

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import yagmail


time.sleep(5)

""" Config File reader """
parser = ConfigParser()
parser.read("preferences.ini")

""" ChromeDriver Autoinstaller and Driver Initialization"""
print("Checking and/or downloading newest Chrome Driver. Please wait.")
# Check if the current version of chromedriver exists and if it doesn't exist, download it automatically,
# then add chromedriver to path
chromedriver_autoinstaller.install()
time.sleep(2)
print("Opening browser")
time.sleep(2)
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.get(parser["INIT_SETTINGS"]["address"])

"""freeze program until user logs in to website"""
logged_in = False
while logged_in is not True:
    answer = input("Has log in been completed? (y/n)>> ")
    if answer == "y":
        logged_in = True

try:  # click submit button on trip options page, unless...
    driver.find_element(By.NAME, "n999").click()
except NoSuchElementException:  # submit button has already been clicked
    pass

# initiate an empty list for trip addresses for initial run
trip_list_1 = []

# sets up the loop function for checking website
row = 3  # trip listings start on row 3
row_xpath = (
    "/html/body/div/div[1]/div/div/div[6]/div[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
    "2]/form/table[3]/tbody/tr "
)
listed_trips = driver.find_elements(By.XPATH, row_xpath)
for trip in listed_trips:

    # xpath_prefix variable helps keep other variables shorter
    xpath_prefix = (
        "/html/body/div/div[1]/div/div/div[6]/div[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
        "2]/form/table[3]/tbody/ "
    )

    try:
        if (
                driver.find_element(By.XPATH, f"{xpath_prefix}tr[{row}]/td[3]").text
                != "PROF"
        ):
            trip_addr = driver.find_element(
                By.XPATH, f"{xpath_prefix}tr[{row}]/td[1]/a"
            ).get_attribute("href")
            trip_list_1.append(trip_addr)

    except NoSuchElementException:
        pass
    row += 1

logged_out = False
while logged_out is False:
    # Message will consist of a dictionary of lists
    email_message = {"First Choice": [], "Second Choice": [], "Third Choice": []}

    # go through trip_list_1 and determine which trips meet preferences, then add trip to email message
    for addr in trip_list_1:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(addr)
        time.sleep(2)

        departure = driver.find_element(
            By.XPATH,
            "/html/body/div/div[1]/div/div/div[6]/div[2]/div/table/tbody/tr["
            "2]/td[3]/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[4]/td["
            "5]",
        ).text[:3]
        try:
            trip_show = int(
                driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div/div/div[6]/div["
                    "2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
                    "2]/form/table[5]/tbody/tr/td[2]",
                ).text[-5:-1]
            )
            trip_end = int(
                driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div/div/div[6]/div["
                    "2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
                    "2]/form/table[5]/tbody/tr/td[5]",
                ).text[-5:-1]
            )
        except NoSuchElementException:
            trip_show = int(
                driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div/div/div[6]/div["
                    "2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
                    "2]/form/table[4]/tbody/tr/td[2]",
                ).text[-5:-1]
            )
            trip_end = int(
                driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div/div/div[6]/div["
                    "2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
                    "2]/form/table[4]/tbody/tr/td[5]",
                ).text[-5:-1]
            )

        if (
                parser["FIRST_CHOICE"]["origination"] == departure
                and int(parser["FIRST_CHOICE"]["start_time"]) <= trip_show
                and int(parser["FIRST_CHOICE"]["end_time"]) >= trip_end
        ):
            print("First Choice")
            email_message["First Choice"].append(addr)
        elif (
                parser["SECOND_CHOICE"]["origination"] == departure
                and int(parser["SECOND_CHOICE"]["start_time"]) <= trip_show
                and int(parser["SECOND_CHOICE"]["end_time"]) >= trip_end
        ):
            print("Second Choice")
            email_message["Second Choice"].append(addr)
        elif (
                parser["THIRD_CHOICE"]["origination"] == departure
                and int(parser["THIRD_CHOICE"]["start_time"]) <= trip_show
                and int(parser["THIRD_CHOICE"]["end_time"]) >= trip_end
        ):
            print("Third Choice")
            email_message["Third Choice"].append(addr)
        else:
            print("Not a preferred trip.")

    """ Email Set Up and Send """
    # https://realpython.com/python-send-email/
    email_from = parser["EMAIL_CONFIG"]["email_from"]
    email_to = parser["EMAIL_CONFIG"]["email_to"]
    if email_message == {"First Choice": [], "Second Choice": [], "Third Choice": []}:
        subject = 'Trip Alert - No New Trips'
        body = 'No new trips which meet your preferences available'
    else:
        subject = 'Trip Alert - New Trips Available'
        body = ''
        for k in email_message:
            body += f'{k}\n'
            for x in email_message[k]:
                body += f'{x}\n'

    yag = yagmail.SMTP(email_from)
    contents = body
    yag.send(email_to, subject, contents)

    # wait for specified time with variance, then refresh page
    wait_time = random.randint(0, 300) + int(parser["INIT_SETTINGS"]["wait_time"])
    curr_time = datetime.now()
    cont_time = curr_time + timedelta(0, wait_time)
    print(
        f"Waiting {wait_time} seconds to refresh. Expect page refresh at {cont_time}."
    )
    time.sleep(wait_time)
    print("Refreshing")
    driver.refresh()
    print("Refreshed")

    # list to compare trip_dict_1 to
    trip_list_2 = []

    row = 3  # trip listings start on row 3
    row_xpath = (
        "/html/body/div/div[1]/div/div/div[6]/div[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td["
        "2]/form/table[3]/tbody/tr "
    )
    listed_trips = driver.find_elements(By.XPATH, row_xpath)
    for trip in listed_trips:

        # xpath_prefix variable helps keep other variables shorter
        xpath_prefix = (
            "/html/body/div/div[1]/div/div/div[6]/div[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr["
            "2]/td[2]/form/table[3]/tbody/ "
        )

        try:
            if (
                    driver.find_element(By.XPATH, f"{xpath_prefix}tr[{row}]/td[3]").text
                    != "PROF"
            ):
                trip_addr = driver.find_element(
                    By.XPATH, f"{xpath_prefix}tr[{row}]/td[1]/a"
                ).get_attribute("href")
                trip_list_2.append(trip_addr)

        except NoSuchElementException:
            pass
        row += 1

    # list compare as per https://stackoverflow.com/questions/3462143/get-difference-between-two-lists matt b answer
    print("Generating new list of trips")
    new_trips = [x for x in trip_list_2 if x not in trip_list_1]
    trip_list_1 = new_trips

