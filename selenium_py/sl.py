from lib2to3.pgen2 import driver
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from fake_useragent import UserAgent
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import requests 
from tqdm import tqdm
import sqlite3
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import os

db = sqlite3.connect('server.db', check_same_thread=False)
sql = db.cursor()



url = "https://ochiqbudjet.uz/boards/6/163564"
useragent = UserAgent()
options = webdriver.ChromeOptions()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
options.add_argument(f'user-agent={useragent.random}')
options.headless = True
# options.add_argument("--window-size=1920,1080")
options.add_argument('--ignore-certificate-errors')
# options.add_argument('--allow-running-insecure-content')
# options.add_argument("--disable-extensions")
# options.add_argument("--proxy-server='direct://'")
# options.add_argument("--proxy-bypass-list=*")
# options.add_argument("--start-maximized")
# options.add_argument('--disable-gpu')
#options.add_argument('--disable-dev-sh-usage')
 #options.add_argument('--no-sandbox')
 #options.add_argument('--headless')
options.add_argument('--ignore-ssl-errors')

sql.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(250),
    username VARCHAR(250),
    telegram_id BIGINT,
    status BOOLEAN,
    phone_number TEXT,
    joined DATETIME
)""")

db.commit()

def save_user(bot, phone_number, msg):
    telegram_id = msg.chat.id
    first_name = msg.chat.first_name
    username = msg.chat.username
    status = 0
    joined = datetime.now()

    values = first_name, username, telegram_id, status, phone_number, joined

    use = sql.execute(f"SELECT id FROM users WHERE telegram_id={telegram_id}")
    time.sleep(4)

    if use.fetchone() == None:
        sql.execute(f"INSERT INTO users(first_name, username, telegram_id, status, phone_number, joined) VALUES(?, ?, ?, ?, ?, ?)", values) 
        db.commit()
        return True
    else:
        print('Have this user')
        sql.execute(f" UPDATE users SET phone_number = {phone_number} WHERE telegram_id = {msg.chat.id};")
        db.commit()
        return True

class Vote:
    def __init__(self, bot, msg):
        telegram_id = msg.chat.id
        phone_number = sql.execute(f"SELECT phone_number FROM users WHERE telegram_id={telegram_id}").fetchone()
        
        

        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options)

        self.driver = driver
        self.bot = bot

        
        driver.get(url=url)
        
        self.valid_phone = str(phone_number).replace('(', '').replace(')', '').replace(',', '')

        

        self.phone_number = phone_number

        

        html = driver.page_source

        if self.phone_number == None or self.valid_phone == '' or self.valid_phone == "''":
            bot.send_message(msg.chat.id, 'Iltimos /start ni bosib registratsiyadan o\'ting')
            
            driver.quit()
        else:

            self.server_m = bot.send_message(msg.chat.id, 'Serverdan javob kutilmoqda...')
            
            driver.refresh()
            
            time.sleep(5)

            html = driver.page_source

            if self.parsing(html):
                # Assaign values to total and current values
                self.main(bot, msg)

            else:
                driver.refresh()
                time.sleep(10)

                bot.send_message(msg.chat.id, 'Biroz kuting')

                html_2 = driver.page_source

                if self.parsing(html_2):
                    self.main(bot, msg)
                else:
                    bot.send_message(msg.chat.id, 'Serverdan javob yo\'q, boshqatan urinib koring /start')
            
    
    def main(self, bot, msg):
        # vote_btn click
        self.driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div/div/div[2]/div/div[5]/div[2]/div/a').click()

        time.sleep(2)

        # click to sms verification

        self.driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div[2]/div/div[2]/div/a').click()

        bot.delete_message(msg.chat.id, self.server_m.message_id)
        one_m = bot.send_message(msg.chat.id, 'Bir daqiqa...')

        time.sleep(3)
    
        # phone_num - input fill phone number
        
     
        self.driver.find_element(By.ID, 'phone').send_keys(self.phone_number)

        bot.delete_message(msg.chat.id, one_m.message_id)

        tele_m = bot.send_message(msg.chat.id, 'Telefon nomer kiritilinmoqda...')

        time.sleep(5)

        # Send sms to verifaction

        self.driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div[2]/div/div[2]/form/div[2]/button').click()
    

        form = self.driver.find_element(By.CLASS_NAME, 'form')

        time.sleep(10)

        try:
            error = form.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div[2]/div/div[2]/form/p')
            
            if error:
                bot.delete_message(msg.chat.id, tele_m.message_id)
                bot.send_message(msg.chat.id, 'Siz ovoz bergansiz /start')
                time.sleep(5)
                self.driver.close()

        except:
            bot.delete_message(msg.chat.id, tele_m.message_id)
            msg_key = bot.send_message(msg.chat.id, 'Sms kodni kiriting')
            bot.register_next_step_handler(msg_key, self.sms_verif)



    def sms_verif(self, msg_key):
        input_verif = self.driver.find_element(By.XPATH, '//*[@id="phone"]').send_keys(msg_key.text)

        time.sleep(4)

        self.driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div[2]/div/div[2]/form/div[2]/button').click()

        checked_m = self.bot.send_message(msg_key.chat.id, "Tekshirilmoqda...")

        time.sleep(8)

        try:
            error = self.driver.find_element(By.XPATH, '//*[@id="__layout"]/div/section/div[2]/div/div[2]/form/p')

            if error:
                self.bot.delete_message(msg_key.chat.id, checked_m.message_id)
                self.bot.send_message(msg_key.chat.id, "Notog'ri kod! Boshqatan urinib koring \n /start")
                self.driver.close()
        except:
            self.bot.delete_message(msg_key.chat.id, checked_m.message_id)
            
            sql.execute(f" UPDATE users SET status = 1 WHERE telegram_id = {msg_key.chat.id};")
            db.commit()

            self.bot.send_message(msg_key.chat.id, "Ovoz berganingiz uchun raxmat")

            

            self.driver.close()
            
    
    def parsing(self, html):
        soup = BeautifulSoup(html, 'lxml')
        txt = soup.find('div', class_='pages-title')
        if txt:
            return True

        return False
        
    