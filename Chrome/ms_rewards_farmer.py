import json
import os
import platform
import random
import subprocess
import sys
import time
import urllib.parse
from argparse import ArgumentParser
from datetime import date, datetime,timedelta
from pathlib import Path
import copy
import traceback
import ipapi
import requests
import pyotp
from functools import wraps
from func_timeout import FunctionTimedOut, func_set_timeout
from notifiers import get_notifier
from random_word import RandomWords
from selenium import webdriver
from selenium.common.exceptions import (ElementNotInteractableException, NoAlertPresentException,
                                        NoSuchElementException, SessionNotCreatedException, TimeoutException,
                                        UnexpectedAlertPresentException, JavascriptException,
                                        ElementNotVisibleException, ElementClickInterceptedException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from math import ceil
from exceptions import *


# Define user-agents
PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36' #Edg/112.0.1722.58
MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 12; SM-N9750) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 EdgA/112.0.1722.46'

POINTS_COUNTER = 0

# Global variables
# added accounts when finished or those have same date as today date in LOGS at beginning.
FINISHED_ACCOUNTS = []
ERROR = True  # A flag for when error occurred.
# A flag for when the account has mobile bing search, it is useful for accounts level 1 to pass mobile.
MOBILE = True
CURRENT_ACCOUNT = None  # save current account into this variable when farming.
LOGS = {}  # Dictionary of accounts to write in 'logs_accounts.txt'.
FAST = False  # When this variable set True then all possible delays reduced.
SUPER_FAST = False  # fast but super
BASE_URL = "https://rewards.bing.com/"


auto_redeem_counter = 0


def browserSetup() -> WebDriver:
    """Create Chrome browser"""
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    
    project_pathname = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))        
    extension_path=project_pathname+"/extension"
    
    if ARGS.edge:
        options = EdgeOptions()
    else:
        options = ChromeOptions()
        
    if ARGS.session or ARGS.account_browser:
        options.add_argument(
                f'--user-data-dir={Path(__file__).parent}/Profiles/{CURRENT_ACCOUNT}/PC')

    #----    
    # options.add_argument("user-agent=" + user_agent)
    options.add_argument('lang=' + LANG.split("-")[0])
    options.add_argument('--disable-blink-features=AutomationControlled')
    #---

    prefs = {"profile.default_content_setting_values.geolocation": 2,
             "credentials_enable_service": False,
             "profile.password_manager_enabled": False,
             "webrtc.ip_handling_policy": "disable_non_proxied_udp",
             "webrtc.multiple_routes_enabled": False,
             "webrtc.nonproxied_udp_enabled": False}
    prefs["profile.managed_default_content_settings.images"] = 2
    

    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    #-----
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    #-----

    options.add_argument('log-level=3')
    options.add_argument('--load-extension={}'.format(extension_path))

    # window Position Set ----------
    # options.add_argument("window-position=1000,500")
    if ARGS.incognito:
        options.add_argument("--incognito")

    if ARGS.edge:
        browser = webdriver.Edge(options=options) if ARGS.no_webdriver_manager else webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()), options=options)
    else:
        browser = webdriver.Chrome(options=options) if ARGS.no_webdriver_manager else webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options)
        stealth(browser,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        
    #Windows size    
    browser.set_window_size(500, 520)
    return browser

def farmer():
    """function that runs other functions to farm."""
    global ERROR, MOBILE, CURRENT_ACCOUNT, STARTING_POINTS  # pylint: disable=global-statement
    
    try:
        for account in ACCOUNTS:
            CURRENT_ACCOUNT = account['username']
            if CURRENT_ACCOUNT in FINISHED_ACCOUNTS:
                continue
            if LOGS[CURRENT_ACCOUNT]["Last check"] != str(date.today()):
                LOGS[CURRENT_ACCOUNT]["Last check"] = str(date.today())
                updateLogs()
                
            prYellow('********************' +   CURRENT_ACCOUNT + '********************')
            
            if not LOGS[CURRENT_ACCOUNT]['PC searches']:
                browser = browserSetup()
                print('[LOGIN]', 'Logging-in...')
                login(browser, account['username'], account['password'], account.get('totpSecret', None))
                prGreen('[LOGIN] Logged-in successfully !')
                
                STARTING_POINTS = POINTS_COUNTER
                prGreen('[POINTS] You have ' + str(POINTS_COUNTER) +   ' points on your account !')
                
                #Browser Open
                goToURL(browser, BASE_URL)
                waitUntilVisible(browser, By.ID, 'app-host', 30)
                remainingSearches, remainingSearchesM = getRemainingSearches(browser)
                MOBILE = bool(remainingSearchesM)
                
                if remainingSearches != 0 or  remainingSearchesM!=0:
                    try :
                            print('[BING]', 'Starting Automatic Bing search Extension...')
                            bingSearches(browser, remainingSearches)
                            prGreen('\n[BING] Finished  Bing searches !!!')
                    except Exception as e:
                        prRed('\n[ERROR] Starting Automatic Bing search Application Exception = ',e)
                    
                        
                    prGreen('\n[BING] Remainings Searches Check & Update....  ')
                    browser.get(BASE_URL)
                    waitUntilVisible(browser, By.ID, 'app-host', 30)
                    remainingSearches, remainingSearchesM = getRemainingSearches(browser)
                    
                    if remainingSearches != 0 or  remainingSearchesM!=0:
                        try :
                            
                                print('[BING]', 'Starting Automatic Bing search Extension...')
                                bingSearches(browser, remainingSearches)
                                prGreen('\n[BING] Finished Bing searches !!!')
                        except Exception as e:
                            prRed('\n[ERROR] Starting Automatic Bing search Application Exception = ',e)
                            
                        prGreen('\n[BING] Remainings Searches Check & Update.. ')
                        browser.get(BASE_URL)
                        waitUntilVisible(browser, By.ID, 'app-host', 30)
                        remainingSearches, remainingSearchesM = getRemainingSearches(browser)
                    
                browser.quit()
        
              
            finishedAccount()
            cleanLogs()
            updateLogs()

    except FunctionTimedOut:
        prRed('[ERROR] Time out raised.\n')
        ERROR = True
        browser.quit()
        farmer()

    except SessionNotCreatedException:
        prBlue('[Driver] Session not created.')
        prBlue(
            '[Driver] Please download correct version of webdriver form link below:')
        prBlue('[Driver] https://chromedriver.chromium.org/downloads')
        input('Press any key to close...')
        sys.exit()

    except KeyboardInterrupt:
        ERROR = True
        browser.quit()
        try:
            input(
                '\n\033[94m[INFO] Farmer paused. Press enter to continue...\033[00m\n')
            farmer()
        except KeyboardInterrupt:
            sys.exit("Force Exit (ctrl+c)")

    except TOTPInvalidException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your TOTP secret was wrong !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your TOTP secret was wrong !')
        checkInternetConnection()
        farmer()

    except AccountLockedException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been locked !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your account has been locked !')
        checkInternetConnection()
        farmer()

    except InvalidCredentialsException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your email or password was not valid !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed('[ERROR] Your Email or password was not valid !')
        checkInternetConnection()
        farmer()

    except UnusualActivityException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        prRed("[ERROR] Unusual activity detected !")
        checkInternetConnection()
        farmer()

    except AccountSuspendedException:
        browser.quit()
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Your account has been suspended'
        LOGS[CURRENT_ACCOUNT]["Today's points"] = 'N/A'
        LOGS[CURRENT_ACCOUNT]["Points"] = 'N/A'
        cleanLogs()
        updateLogs()
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        checkInternetConnection()
        farmer()

    except RegionException:
        browser.quit()
        prRed('[ERROR] Microsoft Rewards is not available in this country or region !')
        input('[ERROR] Press any key to close...')
        os._exit(0)

    except Exception as e:
        if "executable needs to be in PATH" in str(e):
            prRed('[ERROR] WebDriver not found.\n')
            prRed(str(e))
            input("Press Enter to close...")
            os._exit(0)
        if ARGS.error:
            traceback.print_exc()
        print('\n')
        ERROR = True
        if browser is not None:
            browser.quit()
        checkInternetConnection()
        farmer()

    else:

        FINISHED_ACCOUNTS.clear()


def main():
    """main"""
    global LANG, GEO, TZ, ARGS  # pylint: disable=global-statement
    os.system('color')
    ARGS = argumentParser()

    logo()
    loadAccounts()

    LANG, GEO, TZ = getCCodeLangAndOffset()
    if ARGS.account_browser:
        prBlue(f"\n[INFO] Opening session for {ARGS.account_browser[0]}")
        browser = accountBrowser(ARGS.account_browser[0])
        input("Press Enter to close when you finished...")
        if browser is not None:
            browser.quit()
    run_at = None

    if run_at is not None:
        prBlue(f"\n[INFO] Farmer will start at {run_at}")
        while True:
            if datetime.now().strftime("%H:%M") == run_at:

                start = time.time()
                logs()
                farmer()
                if not ARGS.everyday:
                    break
            time.sleep(30)
    else:
        start = time.time()

        logs()
        farmer()
    end = time.time()
    delta = end - start
    hour, remain = divmod(delta, 3600)
    minutes, sec = divmod(remain, 60)
    
    print(f"Farmer finished in: {hour:02.0f}:{minutes:02.0f}:{sec:02.0f}")
    print(f"Farmer finished on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    LOGS["Elapsed time"] = f"{hour:02.0f}:{minutes:02.0f}:{sec:02.0f}"
    
    updateLogs()

    if ARGS.on_finish:
        plat = platform.system()
        if ARGS.on_finish == "shutdown":
            if plat == "Windows":
                os.system("shutdown /s /t 10")
            elif plat == "Linux":
                os.system("systemctl poweroff")
        elif ARGS.on_finish == "sleep":
            if plat == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif plat == "Linux":
                os.system("systemctl suspend")
        elif ARGS.on_finish == "hibernate":
            if plat == "Windows":
                os.system("shutdown /h")
            elif plat == "Linux":
                os.system("systemctl hibernate")
        elif ARGS.on_finish == "exit":
            return
    input('Press enter to close the program...')


def bingSearches(browser: WebDriver, numberOfSearches: int, isMobile: bool = False):
    """Search Bing"""
    #Ref :https://www.geeksforgeeks.org/python-opening-multiple-tabs-using-selenium/
    
    extension_id="lnikijajdcgnahajfbjffalgnikejicd"#ehpnglljgijenbiknlgpcbnnmhfdgbam
    browser.implicitly_wait(105)
    # Lets open google.com in the first tab
    browser.get(f"chrome-extension://{extension_id}/popup.html")
    time.sleep(105)
    


def calculateSleep(default_sleep: int):
    """
    Sleep calculated with this formular:
    on FAST: random.uniform((default_sleep/2) * 0.5, (default_sleep/2) * 1.5)
    on SUPER_FAST: random.uniform((default_sleep/4) * 0.5, (default_sleep/4) * 1.5)
    else: default_sleep
    """
    if SUPER_FAST:
        return random.uniform((default_sleep / 4) * 0.5, (default_sleep / 4) * 1.5)#change
    elif FAST:
        return random.uniform((default_sleep / 2) * 0.5, (default_sleep / 2) * 1.5)
    else:
        return default_sleep
    
def getRemainingSearches(browser: WebDriver):
    """get remaining searches"""
    dashboard = getDashboardData(browser)
    searchPoints = 1
    counters = dashboard['userStatus']['counters']
    if not 'pcSearch' in counters:
        return 0, 0
    progressDesktop = counters['pcSearch'][0]['pointProgress'] + \
        counters['pcSearch'][1]['pointProgress']
    targetDesktop = counters['pcSearch'][0]['pointProgressMax'] + \
        counters['pcSearch'][1]['pointProgressMax']
    if targetDesktop == 33:
        # Level 1 EU
        searchPoints = 3
    elif targetDesktop == 55:
        # Level 1 US
        searchPoints = 5
    elif targetDesktop == 102:
        # Level 2 EU
        searchPoints = 3
    elif targetDesktop >= 170:
        # Level 2 US
        searchPoints = 5
    remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
    remainingMobile = 0
    if dashboard['userStatus']['levelInfo']['activeLevel'] != "Level1":
        progressMobile = counters['mobileSearch'][0]['pointProgress']
        targetMobile = counters['mobileSearch'][0]['pointProgressMax']
        remainingMobile = int((targetMobile - progressMobile) / searchPoints)
        
        #------------Update Today Earning Point------
        LOGS[CURRENT_ACCOUNT]['Earning_Points'] ='PC-'+str(progressDesktop) + '(' + str(targetDesktop) + ') || PH- '  + str(progressMobile) + '(' + str(targetMobile)+ ')'
    else:
        LOGS[CURRENT_ACCOUNT]['Earning_Points'] =' Level-1 ' 
        
    return remainingDesktop, remainingMobile

def logs():
    """Read logs and check whether account farmed or not"""
    global LOGS  # pylint: disable=global-statement
    shared_items = []
    try:
        # Read datas on 'logs_accounts.txt'
        LOGS = json.load(
            open(f"{Path(__file__).parent}/Logs_{ACCOUNTS_PATH.stem}.txt", "r"))
        LOGS.pop("Elapsed time", None)
        # sync accounts and logs file for new accounts or remove accounts from logs.
        for user in ACCOUNTS:
            shared_items.append(user['username'])
            if not user['username'] in LOGS.keys():
                LOGS[user["username"]] = {"Last check": "",
                                          "Today's points": 0,
                                          "Points": 0}
        if shared_items != LOGS.keys():
            diff = LOGS.keys() - shared_items
            for accs in list(diff):
                del LOGS[accs]

        # check that if any of accounts has farmed today or not.
        for account in LOGS.keys():
            if LOGS[account]["Last check"] == str(date.today()) and list(LOGS[account].keys()) == ['Last check',
                                                                                                   "Today's points",
                                                                                                   'Points']:
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == 'Your account has been suspended':
                FINISHED_ACCOUNTS.append(account)
            elif LOGS[account]['Last check'] == str(date.today()) and list(LOGS[account].keys()) == [
                'Last check',
                "Today's points",
                'Points',
                'Daily',
                'Punch cards',
                'More promotions',
                'MSN shopping game',
                'PC searches'
            ]:
                continue
            else:
                LOGS[account]['Daily'] = False
                LOGS[account]['Punch cards'] = False
                LOGS[account]['More promotions'] = False
                LOGS[account]['MSN shopping game'] = False
                LOGS[account]['PC searches'] = False
            if not isinstance(LOGS[account]["Points"], int):
                LOGS[account]["Points"] = 0
        updateLogs()
        prGreen('\n[LOGS] Logs loaded successfully.\n')
    except FileNotFoundError:
        prRed(f'\n[LOGS] "Logs_{ACCOUNTS_PATH.stem}.txt" file not found.')
        LOGS = {}
        for account in ACCOUNTS:
            LOGS[account["username"]] = {"Last check": "",
                                         "Today's points": 0,
                                         "Points": 0,
                                         "Daily": False,
                                         "Punch cards": False,
                                         "More promotions": False,
                                         "MSN shopping game": False,
                                         "PC searches": False,
                                         "Earning_Points":"PC/PH - 0"}
        updateLogs()
        prGreen(f'[LOGS] "Logs_{ACCOUNTS_PATH.stem}.txt" created.\n')

#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------

def retry_on_500_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        driver: WebDriver = args[0]
        error_codes = ["HTTP ERROR 500", "HTTP ERROR 502",
                       "HTTP ERROR 503", "HTTP ERROR 504", "HTTP ERROR 505"]
        status_code = "-"
        result = function(*args, **kwargs)
        while True:
            try:
                status_code = driver.execute_script(
                    "return document.readyState;")
                if status_code == "complete" and not any(error_code in driver.page_source for error_code in error_codes):
                    return result
                elif status_code == "loading":
                    return result
                else:
                    raise Exception("Page not loaded")
            except Exception as e:
                # Check if the page contains 500 errors
                if any(error_code in driver.page_source for error_code in error_codes):
                    driver.refresh()  # Recursively refresh
                else:
                    raise Exception(
                        f"another exception occurred during handling 500 errors with status '{status_code}': {e}")
    return wrapper

@retry_on_500_errors
def goToURL(browser: WebDriver, url: str):
    browser.get(url)

# Define login function
def login(browser: WebDriver, email: str, pwd: str, totpSecret: str, isMobile: bool = False):

    def answerToBreakFreeFromPassword():
        # Click No thanks on break free from password question
        time.sleep(2)
        browser.find_element(By.ID, "iCancel").click()
        time.sleep(5)

    def answerToSecurityQuestion():
        # Click Looks good on security question
        time.sleep(2)
        browser.find_element(By.ID, 'iLooksGood').click()
        time.sleep(5)

    def answerUpdatingTerms():
        # Accept updated terms
        time.sleep(2)
        browser.find_element(By.ID, 'iNext').click()
        time.sleep(5)

    def waitToLoadBlankPage():
        time.sleep(calculateSleep(10))
        wait = WebDriverWait(browser, 10)
        wait.until(ec.presence_of_element_located((By.TAG_NAME, "body")))
        wait.until(ec.presence_of_all_elements_located)
        wait.until(ec.title_contains(""))
        wait.until(ec.presence_of_element_located(
            (By.CSS_SELECTOR, "html[lang]")))
        wait.until(lambda driver: driver.execute_script(
            "return document.readyState") == "complete")

    def acceptNewPrivacy():
        time.sleep(3)
        waitUntilVisible(browser, By.ID, "id__0", 15)
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        waitUntilClickable(browser, By.ID, "id__0", 15)
        browser.find_element(By.ID, "id__0").click()
        WebDriverWait(browser, 25).until_not(
            ec.visibility_of_element_located((By.ID, "id__0")))
        time.sleep(5)

    def answerTOTP(totpSecret):
        """Enter TOTP code and submit"""
        if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
            if totpSecret is not None:
                # Enter TOTP code
                totpCode = pyotp.TOTP(totpSecret).now()
                browser.find_element(
                    By.ID, "idTxtBx_SAOTCC_OTC").send_keys(totpCode)
                print('[LOGIN]', 'Writing TOTP code...')
                # Click submit
                browser.find_element(By.ID, 'idSubmit_SAOTCC_Continue').click()
            else:
                print('[LOGIN]', 'TOTP code required but no secret was provided.')
            # Wait 5 seconds
            time.sleep(5)
            if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
                raise TOTPInvalidException

    # Close welcome tab for new sessions
    if ARGS.session:
        time.sleep(2)
        if len(browser.window_handles) > 1:
            current_window = browser.current_window_handle
            for handler in browser.window_handles:
                if handler != current_window:
                    browser.switch_to.window(handler)
                    time.sleep(0.5)
                    browser.close()
            browser.switch_to.window(current_window)
    time.sleep(1)
    # Access to bing.com
    goToURL(browser, 'https://login.live.com/')
    # Check if account is already logged in
    if ARGS.session:
        if browser.title == "":
            waitToLoadBlankPage()
        if browser.title == "Microsoft account privacy notice" or isElementExists(browser, By.XPATH, '//*[@id="interruptContainer"]/div[3]/div[3]/img'):
            acceptNewPrivacy()
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            answerUpdatingTerms()
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            answerToSecurityQuestion()
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc") or browser.title == "Break free from your passwords":
            answerToBreakFreeFromPassword()
        if browser.title == 'Microsoft account | Home' or isElementExists(browser, By.ID, 'navs_container'):
            prGreen('[LOGIN] Account already logged in !')
            RewardsLogin(browser)
            print('[LOGIN]', 'Ensuring login on Bing...')
            checkBingLogin(browser, isMobile)
            return
        elif browser.title == 'Your account has been temporarily suspended' or browser.current_url.startswith("https://account.live.com/Abuse"):
            raise AccountLockedException
        elif browser.title == "Help us protect your account" or browser.current_url.startswith(
                "https://account.live.com/proofs/Add"):
            handleUnusualActivity(browser, isMobile)
            return
        elif browser.title == "Help us secure your account" or browser.current_url.startswith("https://account.live.com/recover"):
            raise UnusualActivityException
        elif isElementExists(browser, By.ID, 'mectrl_headerPicture') or 'Sign In or Create' in browser.title:
            browser.find_element(By.ID, 'mectrl_headerPicture').click()
            waitUntilVisible(browser, By.ID, 'i0118', 15)
            if isElementExists(browser, By.ID, 'i0118'):
                browser.find_element(By.ID, "i0118").send_keys(pwd)
                time.sleep(2)
                browser.find_element(By.ID, 'idSIButton9').click()
                time.sleep(5)
                answerTOTP(totpSecret)
                prGreen('[LOGIN] Account logged in again !')
                RewardsLogin(browser)
                print('[LOGIN]', 'Ensuring login on Bing...')
                checkBingLogin(browser, isMobile)
                return
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'loginHeader', 10)
    # Enter email
    print('[LOGIN]', 'Writing email...')
    browser.find_element(By.NAME, "loginfmt").send_keys(email)
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 2 seconds
    time.sleep(calculateSleep(5))
    if isElementExists(browser, By.ID, "usernameError"):
        raise InvalidCredentialsException
    # Wait complete loading
    waitUntilVisible(browser, By.ID, 'i0118', 10)
    # Enter password
    time.sleep(3)
    browser.find_element(By.ID, "i0118").send_keys(pwd)
    # browser.execute_script("document.getElementById('i0118').value = '" + pwd + "';")
    print('[LOGIN]', 'Writing password...')
    # Click next
    browser.find_element(By.ID, 'idSIButton9').click()
    # Wait 5 seconds
    time.sleep(5)
    if isElementExists(browser, By.ID, "passwordError"):
        raise InvalidCredentialsException
    answerTOTP(totpSecret)
    try:
        if ARGS.session:
            # Click Yes to stay signed in.
            browser.find_element(By.ID, 'idSIButton9').click()
        else:
            # Click No.
            browser.find_element(By.ID, 'idBtn_Back').click()
    except NoSuchElementException:
        # Check for if account has been locked.
        if (
            browser.title == "Your account has been temporarily suspended" or
            isElementExists(browser, By.CLASS_NAME, "serviceAbusePageContainer  PageContainer") or
            browser.current_url.startswith("https://account.live.com/Abuse")
        ):
            raise AccountLockedException
        elif browser.title == "Help us protect your account" or \
                browser.current_url.startswith("https://account.live.com/proofs/Add"):
            handleUnusualActivity(browser, isMobile)
            return
        elif browser.title == "Help us secure your account" or browser.current_url.startswith("https://account.live.com/recover"):
            raise UnusualActivityException
    else:
        if browser.title == "Microsoft account privacy notice" or isElementExists(browser, By.XPATH, '//*[@id="interruptContainer"]/div[3]/div[3]/img'):
            acceptNewPrivacy()
        if browser.title == "":
            waitToLoadBlankPage()
        if browser.title == "We're updating our terms" or isElementExists(browser, By.ID, 'iAccrualForm'):
            answerUpdatingTerms()
        if browser.title == 'Is your security info still accurate?' or isElementExists(browser, By.ID, 'iLooksGood'):
            answerToSecurityQuestion()
        # Click No thanks on break free from password question
        if isElementExists(browser, By.ID, "setupAppDesc") or browser.title == "Break free from your passwords":
            answerToBreakFreeFromPassword()
    # Wait 5 seconds
    time.sleep(5)
    # Click Security Check
    print('[LOGIN]', 'Passing security checks...')
    try:
        browser.find_element(By.ID, 'iLandingViewAction').click()
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    # Wait complete loading
    try:
        waitUntilVisible(browser, By.ID, 'KmsiCheckboxField', 10)
    except TimeoutException as e:
        pass
    # Click next
    try:
        browser.find_element(By.ID, 'idSIButton9').click()
        # Wait 5 seconds
        time.sleep(5)
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    print('[LOGIN]', 'Logged-in !')
    # Check Microsoft Rewards
    print('[LOGIN] Logging into Microsoft Rewards...')
    RewardsLogin(browser)
    # Check Login
    print('[LOGIN]', 'Ensuring login on Bing...')
    checkBingLogin(browser, isMobile)

    
def RewardsLogin(browser: WebDriver):
    """Login into Rewards"""
    goToURL(browser, BASE_URL)
    try:
        time.sleep(calculateSleep(10))
        # click on sign up button if needed
        if isElementExists(browser, By.ID, "start-earning-rewards-link"):
            browser.find_element(By.ID, "start-earning-rewards-link").click()
            time.sleep(5)
            browser.refresh()
            time.sleep(5)
    except:
        pass
    if browser.title == "Help us protect your account" or \
            browser.current_url.startswith("https://account.live.com/proofs/Add"):
        handleUnusualActivity(browser)
    time.sleep(calculateSleep(10))
    # Check for ErrorMessage
    try:
        browser.find_element(By.ID, 'error').is_displayed()
        # Check wheter account suspended or not
        if browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute(
                'innerHTML') == ' Uh oh, it appears your Microsoft Rewards account has been suspended.':
            raise AccountSuspendedException
        # Check whether Rewards is available in your region or not
        elif browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute(
                'innerHTML') == 'Microsoft Rewards is not available in this country or region.':
            raise RegionException
        else:
            error_text = browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute("innerHTML")
            prRed(f"[ERROR] {error_text}")
            raise DashboardException
    except NoSuchElementException:
        pass
    handleFirstVisit(browser)


@func_set_timeout(300)
def checkBingLogin(browser: WebDriver, isMobile: bool = False):
    """Check if logged in to Bing"""

    def getEmailPass():
        for account in ACCOUNTS:
            if account["username"] == CURRENT_ACCOUNT:
                return account["username"], account["password"], account.get("totpSecret", None)

    def loginAgain():
        waitUntilVisible(browser, By.ID, 'loginHeader', 10)
        print('[LOGIN]', 'Writing email...')
        email, pwd, totpSecret = getEmailPass()
        browser.find_element(By.NAME, "loginfmt").send_keys(email)
        browser.find_element(By.ID, 'idSIButton9').click()
        time.sleep(calculateSleep(5))
        waitUntilVisible(browser, By.ID, 'loginHeader', 10)
        browser.find_element(By.ID, "i0118").send_keys(pwd)
        print('[LOGIN]', 'Writing password...')
        browser.find_element(By.ID, 'idSIButton9').click()
        time.sleep(5)
        # Enter TOTP code if needed
        if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
            if totpSecret is not None:
                # Enter TOTP code
                totpCode = pyotp.TOTP(totpSecret).now()
                browser.find_element(
                    By.ID, "idTxtBx_SAOTCC_OTC").send_keys(totpCode)
                print('[LOGIN]', 'Writing TOTP code...')
                # Click submit
                browser.find_element(By.ID, 'idSubmit_SAOTCC_Continue').click()
            else:
                print('[LOGIN]', 'TOTP code required but no secret was provided.')
            # Wait 5 seconds
            time.sleep(5)
            if isElementExists(browser, By.ID, 'idTxtBx_SAOTCC_OTC'):
                raise TOTPInvalidException
        if isElementExists(browser, By.ID, "idSIButton9"):
            if ARGS.session:
                # Click Yes to stay signed in.
                browser.find_element(By.ID, 'idSIButton9').click()
            else:
                # Click No.
                browser.find_element(By.ID, 'idBtn_Back').click()
        goToURL(browser, "https://bing.com/")

    global POINTS_COUNTER  # pylint: disable=global-statement
    goToURL(browser, 'https://bing.com/')
    time.sleep(calculateSleep(15))
    # try to get points at first if account already logged in
    if ARGS.session:
        try:
            if not isMobile:
                try:
                    POINTS_COUNTER = int(browser.find_element(
                        By.ID, 'id_rc').get_attribute('innerHTML'))
                except ValueError:
                    if browser.find_element(By.ID, 'id_s').is_displayed():
                        browser.find_element(By.ID, 'id_s').click()
                        time.sleep(calculateSleep(15))
                        checkBingLogin(browser, isMobile)
                    time.sleep(2)
                    POINTS_COUNTER = int(
                        browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
            else:
                browser.find_element(By.ID, 'mHamburger').click()
                time.sleep(1)
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except:
            pass
        else:
            return None
    # Accept Cookies
    try:
        browser.find_element(By.ID, 'bnp_btn_accept').click()
    except:
        pass
    if isMobile:
        # close bing app banner
        if isElementExists(browser, By.ID, 'bnp_rich_div'):
            try:
                browser.find_element(
                    By.XPATH, '//*[@id="bnp_bop_close_icon"]/img').click()
            except NoSuchElementException:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'mHamburger').click()
        except:
            try:
                browser.find_element(By.ID, 'bnp_btn_accept').click()
            except:
                pass
            time.sleep(1)
            if isElementExists(browser, By.XPATH, '//*[@id="bnp_ttc_div"]/div[1]/div[2]/span'):
                browser.execute_script("""var element = document.evaluate('/html/body/div[1]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                        element.remove();""")
                time.sleep(5)
            time.sleep(1)
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                pass
        try:
            time.sleep(1)
            browser.find_element(By.ID, 'HBSignIn').click()
            if isElementExists(browser, By.NAME, "loginfmt"):
                loginAgain()
        except:
            pass
        try:
            time.sleep(2)
            browser.find_element(By.ID, 'iShowSkip').click()
            time.sleep(3)
        except:
            if browser.title == "Help us protect your account" or browser.current_url.startswith(
                    "https://account.live.com/proofs/Add"):
                handleUnusualActivity(browser, isMobile)
    # Wait 5 seconds
    time.sleep(5)
    # Refresh page
    goToURL(browser, 'https://bing.com/')
    # Wait 15 seconds
    time.sleep(calculateSleep(15))
    # Update Counter
    try:
        if not isMobile:
            try:
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, 'id_rc').get_attribute('innerHTML'))
            except:
                if browser.find_element(By.ID, 'id_s').is_displayed():
                    browser.find_element(By.ID, 'id_s').click()
                    time.sleep(calculateSleep(15))

                    checkBingLogin(browser, isMobile)
                time.sleep(5)
                POINTS_COUNTER = int(browser.find_element(
                    By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
        else:
            try:
                browser.find_element(By.ID, 'mHamburger').click()
            except:
                try:
                    browser.find_element(By.ID, 'bnp_close_link').click()
                    time.sleep(4)
                    browser.find_element(By.ID, 'bnp_btn_accept').click()
                except:
                    pass
                time.sleep(1)
                browser.find_element(By.ID, 'mHamburger').click()
            time.sleep(1)
            POINTS_COUNTER = int(browser.find_element(
                By.ID, 'fly_id_rc').get_attribute('innerHTML'))
    except:
        checkBingLogin(browser, isMobile)


def handleUnusualActivity(browser: WebDriver, isMobile: bool = False):
    prYellow('[ERROR] Unusual activity detected !')
    if isElementExists(browser, By.ID, "iShowSkip") and ARGS.skip_unusual:
        try:
            waitUntilClickable(browser, By.ID, "iShowSkip")
            browser.find_element(By.ID, "iShowSkip").click()
        except:
            raise UnusualActivityException
        else:
            prGreen('[LOGIN] Account already logged in !')
            RewardsLogin(browser)
            print('[LOGIN]', 'Ensuring login on Bing...')
            checkBingLogin(browser, isMobile)
            return
    else:
        LOGS[CURRENT_ACCOUNT]['Last check'] = 'Unusual activity detected !'
        FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
        updateLogs()
        cleanLogs()
        if ARGS.telegram or ARGS.discord:
            message = createMessage()
            sendReportToMessenger(message)
        input('Press any key to close...')
        os._exit(0)


def handleFirstVisit(browser: WebDriver):
    # Pass The Welcome Page.
    try:
        if isElementExists(browser, By.CLASS_NAME, "rewards-slide"):
            try:
                browser.find_element(
                    By.XPATH, "//div[@class='rewards-slide']//a").click()
                time.sleep(calculateSleep(5))
                progress, total = browser.find_element(
                    By.XPATH, "//div[@class='rewards-slide']//mee-rewards-counter-animation/span").get_attribute("innerHTML").split("/")
                progress = int(progress)
                total = int(total)
                if (progress < total):
                    browser.find_element(
                        By.XPATH, "//mee-rewards-welcome-tour//mee-rewards-slide[contains(@class, 'ng-scope') and not(contains(@class,'ng-hide'))]//mee-rewards-check-mark/../a").click()
                    time.sleep(calculateSleep(5))
            except:
                pass

            browser.find_element(
                By.XPATH, "//button[@data-modal-close-button]").click()
            time.sleep(calculateSleep(5))
    except:
        print('[LOGIN]', "Can't pass the first time quiz.")


def waitUntilVisible(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    """Wait until visible"""
    WebDriverWait(browser, time_to_wait).until(
        ec.visibility_of_element_located((by_, selector)))


def waitUntilClickable(browser: WebDriver, by_: By, selector: str, time_to_wait: int = 10):
    """Wait until clickable"""
    WebDriverWait(browser, time_to_wait).until(
        ec.element_to_be_clickable((by_, selector)))


def waitUntilQuestionRefresh(browser: WebDriver):
    """Wait until question refresh"""
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_elements(By.CLASS_NAME, 'rqECredits')[0]
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False


def waitUntilQuizLoads(browser: WebDriver):
    """Wait until quiz loads"""
    tries = 0
    refreshCount = 0
    while True:
        try:
            browser.find_element(
                By.XPATH, '//*[@id="currentQuestionContainer"]')
            return True
        except:
            if tries < 10:
                tries += 1
                time.sleep(0.5)
            else:
                if refreshCount < 5:
                    browser.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False



def findBetween(s: str, first: str, last: str) -> str:
    """Find between"""
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def getCCodeLangAndOffset() -> tuple:
    """Get lang, geo, time zone"""
    try:
        nfo = ipapi.location()
        lang = nfo['languages'].split(',')[0]
        geo = nfo['country']
        tz = str(round(int(nfo['utc_offset']) / 100 * 60))
        return lang, geo, tz
    # Due to ipapi limitations it will default to US
    except:
        return 'en-US', 'US', '-480'


def getDashboardData(browser: WebDriver) -> dict:
    """Get dashboard data"""
    tries = 0
    dashboard = None
    while not dashboard and tries <= 5:
        try:
            dashboard = findBetween(browser.find_element(By.XPATH, '/html/body').get_attribute('innerHTML'),
                                    "var dashboard = ",
                                    ";\n        appDataModule.constant(\"prefetchedDashboard\", dashboard);")
            dashboard = json.loads(dashboard)
        except json.decoder.JSONDecodeError:
            tries += 1
            if tries == 6:
                raise Exception("[ERROR] Could not get dashboard")
            browser.refresh()
            waitUntilVisible(browser, By.ID, 'app-host', 30)
    return dashboard

def isElementExists(browser: WebDriver, _by: By, element: str) -> bool:
    """Returns True if given element exists else False"""
    try:
        browser.find_element(_by, element)
    except NoSuchElementException:
        return False
    return True


def accountBrowser(chosen_account: str):
    """Setup browser for chosen account"""
    global CURRENT_ACCOUNT  # pylint: disable=global-statement
    for account in ACCOUNTS:
        if account["username"].lower() == chosen_account.lower():
            CURRENT_ACCOUNT = account["username"]
            break
    else:
        return None
    browser = browserSetup(False, PC_USER_AGENT)
    return browser


def argumentParser():
    """getting args from command line"""

    def isValidTime(validtime: str):
        """check the time format and return the time if it is valid, otherwise return parser error"""
        try:
            t = datetime.strptime(validtime, "%H:%M").strftime("%H:%M")
        except ValueError:
            parser.error("Invalid time format, use HH:MM")
        else:
            return t

    def isSessionExist(session: str):
        """check if the session is valid and return the session if it is valid, otherwise return parser error"""
        if Path(f"{Path(__file__).parent}/Profiles/{session}").exists():
            return session
        else:
            parser.error(f"Session not found for {session}")

    parser = ArgumentParser(
        description=f" Microsoft Rewards Farmer ",
        allow_abbrev=False,
        usage="You may use execute the program with the default config or use arguments to configure available options."
    )
    parser.add_argument('--incognito',
                        action='store_true',
                        help='The code below will open the browser in incognito mode using selinium',
                        required=False)
    
    parser.add_argument('--everyday',
                        action='store_true',
                        help='This argument will make the script run everyday at the time you start.',
                        required=False)
    parser.add_argument('--headless',
                        help='Enable headless browser.',
                        action='store_true',
                        required=False)
    parser.add_argument('--session',
                        help='Creates session for each account and use it.',
                        action='store_true',
                        required=False)
    parser.add_argument('--error',
                        help='Display errors when app fails.',
                        action='store_true',
                        required=False)
    parser.add_argument('--fast',
                        help="Reduce delays where ever it's possible to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--superfast',
                        help="Reduce delays where ever it's possible even further than fast mode to make script faster.",
                        action='store_true',
                        required=False)
    parser.add_argument('--telegram',
                        metavar=('<API_TOKEN>', '<CHAT_ID>'),
                        nargs=2,
                        help='This argument takes token and chat id to send logs to Telegram.',
                        type=str,
                        required=False)
    parser.add_argument('--discord',
                        metavar='<WEBHOOK_URL>',
                        nargs=1,
                        help='This argument takes webhook url to send logs to Discord.',
                        type=str,
                        required=False)
    parser.add_argument('--edge',
                        help='Use Microsoft Edge webdriver instead of Chrome.',
                        action='store_true',
                        required=False)
    parser.add_argument('--account-browser',
                        nargs=1,
                        type=isSessionExist,
                        help='Open browser session for chosen account.',
                        required=False)
    parser.add_argument('--start-at',
                        metavar='<HH:MM>',
                        help='Start the script at the specified time in 24h format (HH:MM).',
                        nargs=1,
                        type=isValidTime)
    parser.add_argument("--on-finish",
                        help="Action to perform on finish from one of the following: shutdown, sleep, hibernate, exit",
                        choices=["shutdown", "sleep", "hibernate", "exit"],
                        required=False,
                        metavar="ACTION")
    parser.add_argument("--redeem",
                        help="Enable auto-redeem rewards based on accounts.json goals.",
                        action="store_true",
                        required=False)
    parser.add_argument("--calculator",
                        help="MS Rewards Calculator",
                        action='store_true',
                        required=False)
    parser.add_argument("--skip-unusual",
                        help="Skip unusual activity detection.",
                        action="store_true",
                        required=False)
    parser.add_argument("--skip-shopping",
                        help="Skip MSN shopping game. Useful for people living in regions which do not support MSN Shopping.",
                        action="store_true",
                        required=False)
    parser.add_argument("--no-images",
                        help="Prevent images from loading to increase performance.",
                        action="store_true",
                        required=False)
    parser.add_argument("--shuffle",
                        help="Randomize the order in which accounts are farmed.",
                        action="store_true",
                        required=False)
    parser.add_argument("--no-webdriver-manager",
                        help="Use system installed webdriver instead of webdriver-manager.",
                        action="store_true",
                        required=False)
    parser.add_argument("--currency",
                        help="Converts your points into your preferred currency.",
                        choices=["EUR", "USD", "AUD", "INR", "GBP", "CAD", "JPY",
                                 "CHF", "NZD", "ZAR", "BRL", "CNY", "HKD", "SGD", "THB"],
                        action="store",
                        required=False)
    parser.add_argument("--virtual-display",
                        help="Use PyVirtualDisplay (intended for Raspberry Pi users).",
                        action="store_true",
                        required=False)
    parser.add_argument("--dont-check-for-updates",
                        help="Prevent script from updating.",
                        action="store_true",
                        required=False)
    parser.add_argument("--repeat-shopping",
                        help="Repeat MSN shopping so it runs twice per account.",
                        action="store_true",
                        required=False)
    parser.add_argument("--skip-if-proxy-dead",
                        help="Skips the account when provided Proxy is dead/ not working",
                        action="store_true",
                        required=False)
    parser.add_argument("--dont-check-internet",
                        help="Prevent script from checking internet connection.",
                        action="store_true",
                        required=False)
    parser.add_argument("--recheck-proxy",
                        help="Rechecks proxy in case you face proxy dead error",
                        action="store_true",
                        required=False)

    args = parser.parse_args()
    if args.superfast or args.fast:
        global SUPER_FAST, FAST  # pylint: disable=global-statement
        SUPER_FAST = args.superfast
        if args.fast and not args.superfast:
            FAST = True
    return args


def updateLogs():
    """update logs"""
    _logs = copy.deepcopy(LOGS)
    for account in _logs:
        if account == "Elapsed time":
            continue
        _logs[account].pop("Redeem goal title", None)
        _logs[account].pop("Redeem goal price", None)
    with open(f'{Path(__file__).parent}/Logs_{ACCOUNTS_PATH.stem}.txt', 'w') as file:
        file.write(json.dumps(_logs, indent=4))


def cleanLogs():
    """clean logs"""
    LOGS[CURRENT_ACCOUNT].pop("Daily", None)
    LOGS[CURRENT_ACCOUNT].pop("Punch cards", None)
    LOGS[CURRENT_ACCOUNT].pop("More promotions", None)
    LOGS[CURRENT_ACCOUNT].pop("MSN shopping game", None)
    LOGS[CURRENT_ACCOUNT].pop("PC searches", None)


def finishedAccount():
    """terminal print when account finished"""
    New_points = POINTS_COUNTER - STARTING_POINTS
    prGreen('[POINTS] You have earned ' + str(New_points) + ' points today !')
    prGreen('[POINTS] You are now at ' + str(POINTS_COUNTER) + ' points !\n')

    FINISHED_ACCOUNTS.append(CURRENT_ACCOUNT)
    if LOGS[CURRENT_ACCOUNT]["Points"] > 0 and POINTS_COUNTER >= LOGS[CURRENT_ACCOUNT]["Points"]:
        LOGS[CURRENT_ACCOUNT]["Today's points"] = POINTS_COUNTER - \
            LOGS[CURRENT_ACCOUNT]["Points"]
    else:
        LOGS[CURRENT_ACCOUNT]["Today's points"] = New_points
    LOGS[CURRENT_ACCOUNT]["Points"] = POINTS_COUNTER


def checkInternetConnection():
    """Check if you're connected to the inter-web superhighway"""
    if ARGS.dont_check_internet:
        return
    system = platform.system()
    while True:
        try:
            if system == "Windows":
                subprocess.check_output(
                    ["ping", "-n", "1", "8.8.8.8"], timeout=5)
            elif system == "Linux":
                subprocess.check_output(
                    ["ping", "-c", "1", "8.8.8.8"], timeout=5)
            return
        except subprocess.TimeoutExpired:
            prRed("[ERROR] No internet connection.")
            time.sleep(1)
        except FileNotFoundError:
            return
        except:
            return


def prRed(prt):
    """colour print"""
    print(f"\033[91m{prt}\033[00m")


def prGreen(prt):
    """colour print"""
    print(f"\033[92m{prt}\033[00m")


def prYellow(prt):
    """colour print"""
    print(f"\033[93m{prt}\033[00m")


def prBlue(prt):
    """colour print"""
    print(f"\033[94m{prt}\033[00m")


def prPurple(prt):
    """colour print"""
    print(f"\033[95m{prt}\033[00m")


def logo():
    """logo"""
    prRed("""BING AUTOMATION SYSTEM""")


def loadAccounts():
    """get or create accounts.json"""
    global ACCOUNTS, ACCOUNTS_PATH  # pylint: disable=global-statement
    try:
        ACCOUNTS_PATH = Path(__file__).parent / 'accounts.json'
        ACCOUNTS = json.load(open(ACCOUNTS_PATH, "r"))
    except FileNotFoundError:
        with open(ACCOUNTS_PATH, 'w') as f:
            f.write(json.dumps([{
                "username": "Your Email",
                "password": "Your Password"
            }], indent=4))
        prPurple(f"[ACCOUNT] Accounts credential file '{ACCOUNTS_PATH.name}' created."
                 "\n[ACCOUNT] Edit with your credentials and save, then press any key to continue...")
        input()
        ACCOUNTS = json.load(open(ACCOUNTS_PATH, "r"))
    finally:
        if ARGS.shuffle:
            random.shuffle(ACCOUNTS)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        prRed(str(e))
        input("press Enter to close...")
