import time
from bs4 import BeautifulSoup
from data.constant import *
from tabulate import tabulate
from sdk.logger import add_logger
# from twocaptcha import TwoCaptcha
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver


def add_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("start-maximized")

    return chrome_options


def get_chromedriver():
    chrome_options = add_chrome_options()

    chromedriver = webdriver.Chrome(options=chrome_options)
    return chromedriver


def get_wallets():
    with open("data/wallets.txt", "r") as f:
        return [row.strip() for row in f]


if __name__ == '__main__':

    wallets = get_wallets()
    add_logger()
    driver = get_chromedriver()

    All_balance = 0
    tokens_dict = {}
    try:
        for address in wallets:
            data_tokens = [
                ["chain", "token name", "token value"],
            ]
            data_balances = [
                ["address", "wallet balance", "pool balance"],
            ]

            data_all_balances = [
                ["all balance"],
            ]

            driver.get(url_debank + address)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, XPath_data_updating)))

            page = BeautifulSoup(driver.page_source, "lxml")
            all_balance = page.select_one(selector_all_balance).text.split('+')[0] \
                if '+' in page.select_one(selector_all_balance).text \
                else page.select_one(selector_all_balance).text.split('-')[0]
            wallet_balance = page.select_one(selector_wallet_balance).text

            token_count_len = len(driver.find_elements(By.CLASS_NAME, "db-table-wrappedRow"))

            for token in range(1, token_count_len + 1):
                token_value = page.select_one(selector_token_value.replace("child(1)", f"child({token})")).text
                token_name = page.select_one(selector_token_name.replace("child(1)", f"child({token})", 1)).text

                if token_name in tokens_dict:
                    tokens_dict[token_name] += float(token_value.replace('$', '').replace('<', '').replace(',', ''))
                else:
                    tokens_dict[token_name] = float(token_value.replace('$', '').replace('<', '').replace(',', ''))

                chain = str(driver.find_element(
                    By.CSS_SELECTOR, selector_chain.replace("child(1)", f"child({token})", 1)).get_attribute("href")).split('/')[-2]
                data_tokens.append([token_value, token_name, chain])

            data_balances.append([address,
                                  wallet_balance,
                                  str('$' + str(int(all_balance.replace(',', '').replace('$', ''))
                                                - int(wallet_balance.replace(',', '').replace('$', ''))))
                                  if int(all_balance.replace(',', '').replace('$', '')) -
                                     int(wallet_balance.replace(',', '').replace('$', '')) != 0 else
                                     int(all_balance.replace(',', '').replace('$', '')) -
                                     int(wallet_balance.replace(',', '').replace('$', ''))])

            formatted_table_tokens = tabulate(data_tokens, headers="firstrow", tablefmt="fancy_grid", stralign='center')
            formatted_table_balances = tabulate(data_balances, headers="firstrow", tablefmt="fancy_grid", stralign='center')
            All_balance += int(all_balance.replace(',', '').replace('$', ''))
            print(formatted_table_balances)
            print(formatted_table_tokens)
            print()

        data_all_balances.append(['$' + str(All_balance)])
        for token in tokens_dict:
            data_all_balances[0].append(token)
            data_all_balances[1].append(tokens_dict[token])

        formatted_table_all_balances = tabulate(data_all_balances, headers="firstrow", tablefmt="github", stralign='center')
        print(formatted_table_all_balances)

    except Exception as error:
        print(address, error)
