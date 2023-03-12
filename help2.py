import json
import pickle
import time
import requests
import urllib3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def main():
    new_cookies = False
    if new_cookies:
        # hide the browser and mute all sounds
        options = Options()
        # options.add_argument("--mute-audio")
        # disable logging prints
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # create the web driver
        driver = webdriver.Chrome(options=options)
        driver.get("https://sdarot.buzz/")
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/header/div[2]/div[1]/p/button").click()  # open login box
        username_input = driver.find_element(By.XPATH, "/html/body/header/div[2]/div[1]/div/form/div[1]/div/input")
        username_input.send_keys("omerdagry@gmail.com")
        password_input = driver.find_element(By.XPATH, "/html/body/header/div[2]/div[1]/div/form/div[2]/div/input")
        password_input.send_keys("omerda2820")
        driver.find_element(By.XPATH, "/html/body/header/div[2]/div[1]/div/form/div[4]/button").click()  # login button
        time.sleep(2)
        cookies = requests.sessions.RequestsCookieJar()
        for cookie in driver.get_cookies():
            cookies.set(cookie['name'], cookie['value'])
        with open("sdarot_cookies", "wb") as f:
            f.write(pickle.dumps(cookies))
        driver.quit()
    else:
        with open("sdarot_cookies", "rb") as f:
            cookies = pickle.loads(f.read())
    #
    headers = {"origin": "https://sdarot.buzz", "referer": "https://sdarot.buzz/", "sec-fetch-site": "same-origin"}
    data = json.dumps({"preWatch": "true", "SID": 498, "season": 1, "ep": 5})
    print(data)
    res = requests.post("https://sdarot.buzz/ajax/watch", headers=headers, data=data.encode())
    print(res.status_code)
    print(res.content)
    print(res.raw)
    res2: urllib3.response.HTTPResponse = res.raw
    print(res2.msg)


if __name__ == '__main__':
    main()
