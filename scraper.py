import requests
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pyrebase # Link to API: https://github.com/thisbejim/Pyrebase
from datetime import datetime

chrome_options = Options()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--lang=en")
chrome_options.headless = True
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

config = {
  "apiKey": "AIzaSyCBw-fNgBEqhbgtb8UI3e0stXm0IhUMIis",
  "authDomain": "phone-plan-scraper.firebaseapp.com",
  "databaseURL": "https://phone-plan-scraper.firebaseio.com/",
  "storageBucket": "phone-plan-scraper.appspot.com"
}

firebase = pyrebase.initialize_app(config)

virginURL = 'https://www.virginmobile.ca/en/plans/postpaid.html#!/BYOP/research'
koodoURL = 'https://www.koodomobile.com/rate-plans'
fidoURL = 'https://www.fido.ca/phones/bring-your-own-device?icid=ba-lpmbcnac-pgpfcwrls-1021206'

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"}

def getPlansVirgin():
    driver.get(virginURL)

    element = None
    count = 0
    while(element == None and count != 5):
        try:
            element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "planList"))
            )
        except TimeoutException:
            count += 1
            driver.refresh()

    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')

    planList = soup.find(id="planList")
    plans = planList.find_all(plans="plans")

    stats = []

    for plan in plans:
        price = "$" + (re.search("[0-9]+\.?[0-9]*", plan.find(class_="pricingbox").text)).group()
        data = (re.search("[0-9]+\.?[0-9]*", plan.find(class_="info attClass0").find("span").text))
        if (data == None):
            data = 'Pay per use'
        else: 
            data = data.group() + "GB"
        stats.append((data, price))

    return stats

def getPlansKoodo():
    driver.get(koodoURL)

    element = None
    count = 0
    while(element == None and count != 5):
        try:
            element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "row-list"))
            )
        except:
            count += 1
            driver.refresh()

    if count == 5: return []

    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')

    planList = soup.find(class_="row-list")
    plans = planList.find_all(class_="panel-col-first panel-panel")

    stats = []

    for plan in plans:
        price = "$" + (re.search("[0-9]+\.?[0-9]*", plan.find(class_="koodo-currency").text)).group()
        data = (re.search("[0-9]+\.?[0-9]*", plan.find(class_="views-field views-field-field-data-mobile-value").find('p').text))
        if (data == None):
            data = 'Pay per use'
        else: 
            data = data.group() + "GB"
        stats.append((data, price))

    return stats


def getPlansFido():
    driver.get(fidoURL)

    element = None
    count = 0
    while(element == None and count != 5):
        try:
            element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dsa-dataBlock'))
            )
        except:
            count += 1
            driver.refresh()

    if count == 5: return []

    html = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')

    plans = soup.find_all(class_="dsa-dataBlock")

    stats = []

    for plan in plans:
        price = "$" + (re.search("[0-9]+\.?[0-9]*", plan.find(class_="dsa-dataBlock__tileRightPrice").text).group())
        data = (re.search("[0-9]+\.?[0-9]*", plan.find(class_="dsa-dataBlock__tileLeftFeature").text))
        if (data == None):
            data = 'Pay per use'
        else: 
            data = data.group() + "GB"
        stats.append((data, price))

    return stats

virgin = getPlansVirgin()
koodo = getPlansKoodo()
fido = getPlansFido()

driver.quit()

# Get a reference to the database service
db = firebase.database()

date = datetime.today().strftime('%Y-%m-%d')

for plan in virgin:
    db.child(date).child("Virgin").child("plan").child(plan[0]).set(plan[1])

for plan in koodo:
    db.child(date).child("Koodo").child("plan").child(plan[0]).set(plan[1])

for plan in fido:
    db.child(date).child("Fido").child("plan").child(plan[0]).set(plan[1])

print(date)
print(virgin)
print(koodo)
print(fido)
print("Data uploaded")
