import requests
import sys
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
service_account_file = 'nourishment-9fb659a6f62b.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_file)

gs = gspread.authorize(credentials)
ss_key = '<SPREADSHEET_ID>'
sheet = gs.open_by_key(ss_key).worksheet('<SHEET_NAME>')

base_url = "https://www.sukiya.jp"
scrape_url = base_url + "/menu/in/gyudon/"

print("starting: ", sys.argv[0], ": ", scrape_url)
page = requests.get(scrape_url)
page.encoding = page.apparent_encoding

soup = BeautifulSoup(page.text, 'html.parser')

all_menu = soup.find('dl', id='lnav_menu_in')
all_menu_links = all_menu.find_all('a')

def updateSheet(alphabet, number, value):
    sheet.update_acell(alphabet + str(number), value)

row_number = 1
finished_urls = [
    '/menu/out/gyudon/',
]

start_time = time.time()
for all_menu_link in all_menu_links:
    link = all_menu_link.get('href')
    if link in finished_urls:
        continue

    menu_page = requests.get(base_url + link)
    menu_page.encoding = menu_page.apparent_encoding
    menu_soup = BeautifulSoup(menu_page.text, 'html.parser')
    # カテゴリー名
    category = menu_soup.find('h1').text

    # メニュー商品一覧
    menu_list = menu_soup.find_all('td', class_='cell_product')
    for menu_item in menu_list:
        time.sleep(1)
        print(menu_item)
        try:
            menu_item_links = menu_item.find('dd').find_all('a')
        except:
            menu_item_links = []
        for menu_item_link in menu_item_links:
            menu_item_page = requests.get(base_url+menu_item_link.get('href'))
            menu_item_page.encoding = menu_item_page.apparent_encoding

            menu_item_soup = BeautifulSoup(menu_item_page.text, 'html.parser')

            # 商品名
            try:
                menu_item_title = menu_item_soup.find('h1').text
            except:
                menu_item_title = ''

            menu_item_nutrient_link = menu_item_soup.find('li', id='tab_menu_nutrient').find('a').get('href')
            menu_item_nutrient_page = requests.get(base_url + menu_item_nutrient_link)
            menu_item_nutrient_page.encoding = menu_item_nutrient_page.apparent_encoding
            menu_item_nutrient_soup = BeautifulSoup(menu_item_nutrient_page.text, 'html.parser')
            menu_item_nutrient_table =  menu_item_nutrient_soup.find(class_='sec_nutrient').find('tbody').find_all('tr')

            for menu_item_nutrient in menu_item_nutrient_table:
                time.sleep(2)
                try:
                    amount = menu_item_nutrient.find('th').text
                except:
                    amount = '不明'
                # カテゴリー名
                updateSheet('A', row_number, category)
                # 商品名
                updateSheet('B', row_number, menu_item_title)
                # 量
                updateSheet('C', row_number, amount)
                # URL
                updateSheet('I', row_number, base_url + menu_item_nutrient_link)
                try:
                    menu_item_nutrient_tds = menu_item_nutrient.find_all('td')
                except:
                    menu_item_nutrient_tds = []

                index = 0
                columns = {
                    0: 'D',
                    1: 'E',
                    2: 'F',
                    3: 'G',
                    4: 'H',
                }
                for menu_item_nutrient_td in menu_item_nutrient_tds:
                    #栄養素
                    try:
                        alphabet = columns[index]
                    except:
                        alphabet = ''

                    if alphabet:
                        updateSheet(alphabet, row_number, menu_item_nutrient_td.text)

                    time.sleep(1)
                    index = index + 1
                print(time.time() - start_time, "秒経過")
                row_number = row_number + 1
    finished_urls.append(link)
