from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os


class Nutrients:
    def __init__(self, gFat=0, gCarb=0, gProtein=0):
        self.gFat = gFat
        self.gCarb = gCarb
        self.gProtein = gProtein


class Meal:
    def __init__(self, meal_type="", description="", nutrients=Nutrients()):
        self.meal_type = meal_type
        self.description = description
        self.nutrients = nutrients


def get_menu(link, mail, pwd):
    driver = webdriver.Chrome()
    driver.set_window_size(1500, 800)
    driver.get(link)
    sign_in_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@class='button btn-1'][@data-popup-open='login-register']")
        )
    )
    sign_in_button.click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "popup-login-register"))
    )
    username_field = driver.find_element(By.NAME, "_username")
    username_field.send_keys(mail)
    password_field = driver.find_element(By.NAME, "_password")
    password_field.send_keys(pwd)
    submit_button = driver.find_element(
        By.CSS_SELECTOR, 'input[type="submit"][value="Log in"]'
    )
    submit_button.click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "account-nav"))
    )
    print("Logged in successfully!")
    menu_link = driver.find_element(By.ID, "menu-link")
    menu_link.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Your menu")]'))
    )
    return driver.page_source


def get_meals(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    meals_list = []
    today = soup.find("div", {"data-date": datetime.today().date()})
    meals = today.findAll("div", {"class": "meal"})
    for meal in meals:
        meal_nutrients = Nutrients()
        nutrients = meal.findAll("div", {"class": "nutrient"})
        for nutrient in nutrients:
            nutrient_name = nutrient.find_all("div")[0].get_text()
            nutrient_value = nutrient.find_all("div")[1].get_text()[:-2]
            if nutrient_name == "fat":
                meal_nutrients.gFat = float(nutrient_value)
            if nutrient_name == "carbohydrate":
                meal_nutrients.gCarb = float(nutrient_value)
            if nutrient_name == "protein":
                meal_nutrients.gProtein = float(nutrient_value)
        meal_type = meal.find("div", {"class": "type"}).get_text()
        description = meal.find("div", {"class": "description"}).text
        meals_list.append(
            Meal(str(meal_type), description.replace("*", ""), meal_nutrients)
        )
    return meals_list


def get_totals(meals):
    total_fats = 0
    total_carbs = 0
    total_proteins = 0
    for meal in meals:
        total_fats = total_fats + meal.nutrients.gFat
        total_carbs = total_carbs + meal.nutrients.gCarb
        total_proteins = total_proteins + meal.nutrients.gProtein
    return {
        "totalFats": round(total_fats, 2),
        "totalCarbs": round(total_carbs, 2),
        "totalProteins": round(total_proteins, 2),
    }


def prepare_content(meals, totals):
    content = """"""
    for meal in meals:
        content += f"""{meal.meal_type}
--------------------
Description: {meal.description}
Fats: {meal.nutrients.gFat} grams
Carbohydrates: {meal.nutrients.gCarb} grams
Proteins: {meal.nutrients.gProtein} grams
-------------------------------------------------
"""
    return f"""Total Fats: {totals['totalFats']} grams
Total Carbohydrates: {totals['totalCarbs']} grams
Total Proteins: {totals['totalProteins']} grams
-------------------------------------------------
{content}
"""


def send_mail(mail, pwd, content):
    msg = MIMEText(content)
    msg["Subject"] = f"Daily Nutrients Report - {datetime.today().date()}"
    msg["From"] = mail
    msg["To"] = mail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
      smtp_server.login(mail, pwd)
      smtp_server.sendmail(mail, [mail], msg.as_string())
    print("Message sent!")


def main():
    load_dotenv()
    source = get_menu(
        os.getenv("WEBSITE_LINK"), os.getenv("E_MAIL"), os.getenv("WEBSITE_PASSWORD")
    )
    meals = get_meals(source)
    totals = get_totals(meals)
    content = prepare_content(meals, totals)
    send_mail(os.getenv("E_MAIL"), os.getenv("APPLICATION_PASSWORD"), content)


if __name__ == "__main__":
    main()
