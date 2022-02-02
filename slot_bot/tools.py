import datetime
import time
import logging
import re
import os
import requests
from anticaptchaofficial.geetestproxyless import *
from anticaptchaofficial.recaptchav2proxyless import *

import config

class MainTools:
    def __init__(self):
        self.__db_dict = {
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "database": config.DB_DATABASE
        }
        self.__root = os.path.dirname(os.path.abspath(__file__))
    
    def get_logger(self, logger_name, log_path):
        logger = logging.getLogger(logger_name)
        if not logger.hasHandlers():
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            fileHandler = logging.FileHandler(log_path, mode='a+')
            fileHandler.setFormatter(formatter)

            streamHandler = logging.StreamHandler()
            streamHandler.setFormatter(formatter)

            logger.setLevel(logging.INFO)
            logger.addHandler(fileHandler)
            logger.addHandler(streamHandler)

        return logger

    def create_display(self):
        import os
        from pyvirtualdisplay import Display
        import Xlib.display
        try:
            v_display = Display(visible=0, size=(1360, 731))
            print('Starting virtual display')
            v_display.start()
            import pyautogui
            pyautogui._pyautogui_x11._display = Xlib.display.Display(
                os.environ['DISPLAY']
            )
            return v_display
        except Exception as e:
            print(e)
            return False

    def create_driver(self, phost, pport, puser, ppass):
        from seleniumwire import webdriver
        from selenium.webdriver.chrome.options import Options
        import zipfile

        chrome_options = Options()
        PROXY_HOST = phost
        PROXY_PORT = pport
        PROXY_USER = puser
        PROXY_PASS = ppass
        manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        proxy = '{user}:{password}@{host}:{port}'.format(user=PROXY_USER,password=PROXY_PASS,host=PROXY_HOST,port=PROXY_PORT)
        if proxy:
            pluginfile = 'proxy_auth_plugin.zip'

            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-infobars')
        #chrome_options.add_argument('--disable-dev-shm-usage')
        #chrome_options.add_argument('--disable-browser-side-navigation')
        #chrome_options.add_argument('--disable-gpu')
        #chrome_options.add_argument('--lang=es')
        #chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        #chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--mute-audio')
        chrome_options.binary_location = "/usr/bin/chromium-browser"

        print('creating driver')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.maximize_window()
        return driver

    def login(self, driver, username, password):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            login_button_xpath = "//button[contains(text(),' Log In ')]"
            username_box_xpath = "//input[@name='userName']"
            password_box_xpath = "//input[@name='password']"
            cashier_button_xpath = "//button[contains(text(),'Cashier')]"
            accept_cookies_button_xpath = "//button[contains(text(),'Accept & Close')]"
            driver.get(config.login_url)
            print('Solving login captcha')
            captcha_solved = False
            try:
                ##try recaptcha
                captcha_solved = self.recaptcha_solver(driver,config.ANTICAPTCHA_KEY)
            except:
                ##try geetest
                captcha_solved = self.geetest_solver(driver,config.ANTICAPTCHA_KEY)
            if captcha_solved:
                print('Waiting for login button')
                login_button = WebDriverWait(driver,90).until(EC.presence_of_element_located((By.XPATH,login_button_xpath)))
                if not login_button:
                    print('Login button not found')
                    return False
                time.sleep(3)
                # find login button again (the page refreshes for some reason)
                login_button = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,login_button_xpath)))    
                username_box = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,username_box_xpath)))
                password_box = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,password_box_xpath)))
                username_box.send_keys(username)
                password_box.send_keys(password)
                print('Waiting to click login button')
                time.sleep(5)
                login_button.click()
                page_loaded = WebDriverWait(driver,120).until(EC.presence_of_element_located((By.XPATH,cashier_button_xpath)))
                if not page_loaded:
                    return False
                cookies_button = WebDriverWait(driver,120).until(EC.presence_of_element_located((By.XPATH,accept_cookies_button_xpath)))
                if cookies_button:
                    print('Accepting cookies')
                    cookies_button.click()
                return True
            else:
                return False
        except Exception as e:
            print(e)
            raise

    def check_balance(self, driver):
        try:
            balance = driver.find_elements_by_xpath('//p[@class="top-up__amount__value"]')[0].text
            balance = re.sub(r'£','',balance)
            balance = float(balance)
            return balance
        except Exception as e:
            print(e)
            return False

    def initialize_game(self, driver):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import pyautogui
        try:
            initialized = False
            search_icon_xpath = "//div[contains(@class,'search-icon')]"
            search_bar_xpath = "//input[contains(@placeholder,'Search games')]"
            game_name = 'Mighty Black Knight'
            game_span_xpath = "//span[contains(text(),'{}')]".format(game_name)
            bonus_balance_popup_xpath = "//modal-container//button[contains(text(),'Play')]"

            print('Searching game')
            pyautogui.screenshot(config.BOT_ERROR_PATH + 'searching_game.png')
            search_icon = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,search_icon_xpath)))
            time.sleep(3)
            search_icon.click()
            search_bar = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,search_bar_xpath)))
            time.sleep(3)
            search_bar.send_keys(game_name)
            game_span = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,game_span_xpath)))
            time.sleep(3)
            game_span.click()
            try:
                # wait and click bonus balance popup
                bonus_balance_popup = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,bonus_balance_popup_xpath)))
                print('closing bonus balance popup')
                bonus_balance_popup.click()
            except:
                pass
            maximize_button = self.wait_for_element(self.__root + '/../maximize_game_crop.png',60,0.6)
            pyautogui.click(maximize_button)
            initialized = self.wait_for_element(self.__root + '/../spin_button_crop.png',120,0.6)
            if initialized:
                print('Game initialized')
                return True
            else:
                return False
        except Exception as e:
            print(e)
            raise

    def play_game(self, driver, instance_id):
        import pyautogui
        try:
            print('Playing game')
            game_iframe_xpath = '//iframe[@title="game-iframe-title"]'
            game_iframe = driver.find_element_by_xpath(game_iframe_xpath)
            bb_button_image = self.__root + '/../bb_button_crop.png'
            driver.execute_script('arguments[0].scrollIntoView({block: "center"});', game_iframe)
            coords = self.wait_for_element(bb_button_image,120,0.6)
            print('Clicking BB button')
            pyautogui.click(coords)
            # check balance before playing the game
            current_balance = self.check_balance(driver)
            current_balance = 150 # TODO descomentar en produccion
            # set starting_balance before playing the game
            url = "http://{}/update-instance-field?id={}&field={}&value={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_id, 'starting_balance', str(current_balance))
            response = requests.request("GET", url)
            while 50 < current_balance < 290:
                self.spin_game()
                # check balance after each spin
                current_balance = self.check_balance(driver)
                print(f'Current balance: {current_balance}')
                # update balance after each spin
                url = "http://{}/update-instance-field?id={}&field={}&value={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_id, 'current_balance', str(current_balance))
                response = requests.request("GET", url)
            final_balance = self.check_balance(driver)
            # update final balance
            url = "http://{}/update-instance-field?id={}&field={}&value={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_id, 'final_balance', str(final_balance))
            response = requests.request("GET", url)
            return True, final_balance
        except Exception as e:
            print(e)
            raise

    def spin_game(self):
        import pyautogui
        try:
            fifty_pounds_button_image = self.__root + '/../50_pounds_button_crop.png'
            coords_50 = self.wait_for_element(fifty_pounds_button_image,120,0.95)
            #pyautogui.click(coords_50) # TODO descomentar en produccion
            time.sleep(1)
            print('Clicking 50 pound button')
            #pyautogui.click(coords_50) # TODO descomentar en produccion # clik again
            pyautogui.screenshot(config.BOT_ERROR_PATH + 'testing-play50.png',coords_50) 
            self.wait_for_element(fifty_pounds_button_image,120,0.95)
            time.sleep(30)
            return True
        except Exception as e:
            print(e)
            return False

    def wait_for_element(self, image, timeout, confidence=1.0):
        import pyautogui
        for i in range(timeout):
            coords = pyautogui.locateOnScreen(image, confidence=confidence)
            if coords:
                return coords
            time.sleep(1)
        return False

    def recaptcha_solver(self, driver, anticaptcha_api_key):
        try:
            # obtain captcha frame
            captcha_iframe = driver.find_element_by_xpath('//iframe[contains(@src,"geo.captcha")]')
            # obtain captcha url to solve
            url = captcha_iframe.get_attribute('src')

            # generate a new site key to solve
            text = requests.get(url).text
            # extract site key to send to recaptcha API
            text = re.sub(r'\\n','\n',text)
            site_key = re.findall(r"(?:'sitekey.*:.*?')(.*)(?:',)",text)[-1]

            #initiate solver and send site key to solve
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1)
            solver.set_key(anticaptcha_api_key)
            solver.set_website_url(url)
            solver.set_website_key(site_key)
            recaptcha_response = solver.solve_and_return_solution()
            if recaptcha_response:
                time.sleep(10)
                print('solved')
                # switch to captcha frame and add the HTML code with the response
                driver.switch_to_frame(captcha_iframe)
                driver.execute_script("""document.getElementsByName("g-recaptcha-response")[0].innerHTML = arguments[0]""",recaptcha_response)
                # execute callback to refresh page
                driver.execute_script("""captchaCallback(arguments[0])""")
                time.sleep(5)
                return True
            else:
                print('unable to solve recaptcha')
                return False
        except Exception as e:
            print('Error on solving recaptcha')
            print(e)
            raise

    def geetest_solver(self, driver, api_key):
        """
            Solve Geetest captcha
        :param driver:
        :param api_key:
        :return:
        """
        print("Looking for CAPTCHA presence")
        try:
            iframe = driver.find_element_by_xpath('//iframe[contains(@src,"geo.captcha-delivery")]')
            print("Captcha Found, please wait until solving")
            url = iframe.get_attribute('src')

            stop = 0
            tries = 0
            while stop == 0 and tries < 10:
                req = requests.get(url)

                # extract data to resolve captcha
                reply_url = driver.current_url
                api_server = re.findall(r"(?:initGeetest\({(?:\s+.*?)+api_server: ')(.*?)(?:',)", req.text)[0]
                gt = re.findall(r"(?:initGeetest\({(?:\s+.*?)+gt: ')(.*?)(?:',)", req.text)[0]
                challenge = re.findall(r"(?:initGeetest\({(?:\s+.*?)+challenge: ')(.*?)(?:',)", req.text)[0]

                solver = geetestProxyless()
                solver.set_verbose(1)
                solver.set_key(api_key)
                solver.set_website_url(reply_url)
                solver.set_js_api_domain(api_server)
                solver.set_gt_key(gt)
                solver.set_challenge_key(challenge)
                # make request to anticaptcha api
                geetest_response = solver.solve_and_return_solution()
                if geetest_response:

                    driver.switch_to.frame(iframe)

                    url = 'https://geo.captcha-delivery.com/captcha/check'
                    parameters = {
                        'cid': re.findall(r"(?:'cid='\s*\+\s*encodeURIComponent\(\s*')(.*?)(?:'\s*\);)", driver.page_source)[0],
                        'icid': re.findall(r"(?:'&icid='\s*\+\s*encodeURIComponent\(\s*')(.*?)(?:'\s*\);)", driver.page_source)[0],
                        'ccid': 'null',
                        'geetest-response-challenge': geetest_response['challenge'],
                        'geetest-response-validate': geetest_response['validate'],
                        'geetest-response-seccode': geetest_response['seccode'],
                        'hash': 'C45A0B68F7D5D289EBFE171FB4EC02',
                        'ua': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                        'referer': 'https://www.luckyvip.com/login',
                        'parent_url': 'https://www.luckyvip.com/',
                        'x-forwarded-for': '',
                        'captchaChallenge': re.findall(r'(?:callback=geetest_)(.*?)(?:">)', driver.page_source)[0],
                        's': '33488'
                    }
                    # make request to validate captcha and obtain a new cookie
                    print(req.text)
                    for i in range(10):
                        if 'cookie' in req.text and len(req.text) < 250:
                            break
                        time.sleep(1)
                        # retry 10 times
                        req = requests.get(url=url, params=parameters)
                        print(req.text)

                    if req:
                        # if cookie

                        cookie = {
                            'name': 'datadome',
                            'value': re.findall(r'(?:"datadome=)(.*?)(?:;)', req.text)[0]
                        }
                        driver.switch_to.default_content()
                        # delete old cookie
                        driver.delete_cookie("datadome")
                        # update with new cooke
                        driver.add_cookie(cookie)
                        driver.refresh()
                        time.sleep(10)

                        print("Captcha solved")
                        stop = 1
                else:
                    # if failed, trying again
                    print("Captcha resolution failed, trying again")
                    tries += 1
        except Exception as e:
            print('Error on solving geetest captcha')
            print(e)
            raise

        return True