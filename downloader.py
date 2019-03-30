import time
import os
import json
import pathlib

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC



LOGIN_URL = "https://tobarhiv.72to.ru"
ITEM_ID = "2219629"
TARGET_URL = f"https://tobarhiv.72to.ru/Pages/StorageFiles/StorageFilesList.aspx?ItemId={ITEM_ID}&ItemType=5"
LOGIN = "olya_9019"
PASSWORD = "paroldlybro"

GUIDS_FILE = f"guids_{ITEM_ID}.json"
DOWNLOADS_DIRECTORY = "/home/br0ke/Downloads"


# selectors
LOADING_BAR = "#UpdateProgress"
NEXT_PAGE_BTN = "#MainPlaceHolder__pagingControl__bForward"
SHOW_BTN_FORMAT = "#MainPlaceHolder__storageFilesGridControl__gStorageFiles__bShowViewer_{id}"
GO_TO_FIRST_IMAGE_BTN = "#MainPlaceHolder__storageViewerControl_ToFirstFileBtn"
GO_TO_NEXT_IMAGE_BTN = '#MainPlaceHolder__storageViewerControl_ForwardBtn'


def check_exists_by_css_selector(driver, selector):
    try:
        driver.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return False
    return True


def check_enabled_by_css_selector(driver, selector):
    try:
        return driver.find_element_by_css_selector(selector).is_enabled()
    except NoSuchElementException:
        return False


def wait_until_elem_appear(driver, elem_selector: str, wait_time=30) -> None:
    if driver.find_element_by_css_selector(elem_selector).is_displayed():
        return
    WebDriverWait(driver, wait_time).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, elem_selector))
    )


def wait_until_elem_disappear(driver, elem_selector: str, wait_time=30) -> None:
    if not driver.find_element_by_css_selector(elem_selector).is_displayed():
        return
    WebDriverWait(driver, wait_time).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, elem_selector))
    )



chrome_options = webdriver.ChromeOptions()
chrome_options.headless = False
# below trick saved my life
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--auto-open-devtools-for-tabs')

# Optional argument, if not specified will search path.
driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=chrome_options)
driver.fullscreen_window()

# Scraping steps
driver.get(LOGIN_URL)
time.sleep(2)
element = driver.find_element_by_css_selector("#LoginPnl_UserName")
element.send_keys(LOGIN)
element = driver.find_element_by_css_selector("#LoginPnl_Password")
element.send_keys(PASSWORD)
driver.find_element_by_css_selector("#Login").click()
time.sleep(2)

driver.get(TARGET_URL)
time.sleep(2)

# Set 100 items per page
driver.find_element_by_css_selector("#MainPlaceHolder__pagingControl__ddlRecordsPerPage").click()
time.sleep(2)
driver.find_element_by_css_selector("#MainPlaceHolder__pagingControl__ddlRecordsPerPage > option:nth-child(5)").click()
time.sleep(5)

guids = dict()

# Get list of guids
if pathlib.Path(GUIDS_FILE).exists():
    # Read from file if exists
    with open(GUIDS_FILE) as f:
        guids = json.load(f)
else:
    # Else parse guids from pages
    while True:
        rows = driver.find_elements_by_css_selector('tr.even, tr.odd')

        for i, elem in enumerate(rows):
            # const guid = $(elem).find('td[align="center"] > span ').attr('guid');
            # const filename = $(elem).find('div.preview').attr('title').split('\\').join('_');
            guid = elem.find_element_by_css_selector('td[align="center"] > span').get_attribute('guid')
            filename = elem.find_element_by_css_selector('div.preview').get_attribute('title')
            normalized_filename = filename.replace('\\', '_')
            guids[normalized_filename] = guid
            print(i, guid, normalized_filename)

        if not check_enabled_by_css_selector(driver, NEXT_PAGE_BTN):
            break

        driver.find_element_by_css_selector(NEXT_PAGE_BTN).click()
        time.sleep(5)

    # Save to file
    with open(GUIDS_FILE, 'w') as f:
        json.dump(guids, f)


# Open viewer and go to first image
driver.find_element_by_css_selector(SHOW_BTN_FORMAT.format(id=0)).click()
time.sleep(5)
if check_exists_by_css_selector(driver, GO_TO_FIRST_IMAGE_BTN):
    driver.find_element_by_css_selector(GO_TO_FIRST_IMAGE_BTN).click()
    time.sleep(5)

# Import FileSaver.js as we need saveAs() function
driver.execute_script("""
(function (a, b) { if ("function" == typeof define && define.amd) define([], b); else if ("undefined" != typeof exports) b(); else { b(), a.FileSaver = { exports: {} }.exports } })(this, function () { "use strict"; function b(a, b) { return "undefined" == typeof b ? b = { autoBom: !1 } : "object" != typeof b && (console.warn("Depricated: Expected third argument to be a object"), b = { autoBom: !b }), b.autoBom && /^\s*(?:text\/\S*|application\/xml|\S*\/\S*\+xml)\s*;.*charset\s*=\s*utf-8/i.test(a.type) ? new Blob(["\uFEFF", a], { type: a.type }) : a } function c(b, c, d) { var e = new XMLHttpRequest; e.open("GET", b), e.responseType = "blob", e.onload = function () { a(e.response, c, d) }, e.onerror = function () { console.error("could not download file") }, e.send() } function d(a) { var b = new XMLHttpRequest; return b.open("HEAD", a, !1), b.send(), 200 <= b.status && 299 >= b.status } function e(a) { try { a.dispatchEvent(new MouseEvent("click")) } catch (c) { var b = document.createEvent("MouseEvents"); b.initMouseEvent("click", !0, !0, window, 0, 0, 0, 80, 20, !1, !1, !1, !1, 0, null), a.dispatchEvent(b) } } var f = "object" == typeof window && window.window === window ? window : "object" == typeof self && self.self === self ? self : "object" == typeof global && global.global === global ? global : void 0, a = f.saveAs || ("object" != typeof window || window !== f ? function () { } : "download" in HTMLAnchorElement.prototype ? function (b, g, h) { var i = f.URL || f.webkitURL, j = document.createElement("a"); g = g || b.name || "download", j.download = g, j.rel = "noopener", "string" == typeof b ? (j.href = b, j.origin === location.origin ? e(j) : d(j.href) ? c(b, g, h) : e(j, j.target = "_blank")) : (j.href = i.createObjectURL(b), setTimeout(function () { i.revokeObjectURL(j.href) }, 4E4), setTimeout(function () { e(j) }, 0)) } : "msSaveOrOpenBlob" in navigator ? function (f, g, h) { if (g = g || f.name || "download", "string" != typeof f) navigator.msSaveOrOpenBlob(b(f, h), g); else if (d(f)) c(f, g, h); else { var i = document.createElement("a"); i.href = f, i.target = "_blank", setTimeout(function () { e(i) }) } } : function (a, b, d, e) { if (e = e || open("", "_blank"), e && (e.document.title = e.document.body.innerText = "downloading..."), "string" == typeof a) return c(a, b, d); var g = "application/octet-stream" === a.type, h = /constructor/i.test(f.HTMLElement) || f.safari, i = /CriOS\/[\d]+/.test(navigator.userAgent); if ((i || g && h) && "object" == typeof FileReader) { var j = new FileReader; j.onloadend = function () { var a = j.result; a = i ? a : a.replace(/^data:[^;]*;/, "data:attachment/file;"), e ? e.location.href = a : location = a, e = null }, j.readAsDataURL(a) } else { var k = f.URL || f.webkitURL, l = k.createObjectURL(a); e ? e.location = l : location.href = l, e = null, setTimeout(function () { k.revokeObjectURL(l) }, 4E4) } }); f.saveAs = a.saveAs = a, "undefined" != typeof module && (module.exports = a) });
""")

# Iterate through files
while True:
    wait_until_elem_disappear(driver, LOADING_BAR)

    while True:
        try:
            filename = driver.find_element_by_css_selector(
                '#MainPlaceHolder__storageViewerControl_FilesDropDownList_I'
            ).get_attribute('value')
        except StaleElementReferenceException:
            print('Stale element error')
            time.sleep(5)
            continue
        break

    normalized_filename = filename.replace('\\', '_')
    guid = guids[normalized_filename]
    
    print(normalized_filename, guid)

    if pathlib.Path(DOWNLOADS_DIRECTORY, normalized_filename).exists():
        print(f'Skipping {filename}...')
    else:
        # viewer = driver.find_element_by_css_selector('#MainPlaceHolder__storageViewerControl_DeepZoomImageViewer_seadragonContainer')
        # time.sleep(5)

        url = f"https://tobarhiv.72to.ru/Pages/ImageFile.ashx?level=12&x=0&y=0&tileSize=10000&tileOverlap=1&id={guid}&page=0&rotation=0&searchtext="

        download_script = f'''
        return fetch('{url}',
            {{
                "credentials": "same-origin",
                "headers": {{"accept":"image/webp,image/apng,image/*,*/*;q=0.8","accept-language":"en-US,en;q=0.9"}},
                "referrer": "{TARGET_URL}",
                "referrerPolicy": "no-referrer-when-downgrade",
                "body": null,
                "method": "GET",
                "mode": "cors"
            }}
        ).then(resp => {{
            return resp.blob();
        }}).then(blob => {{
            saveAs(blob, '{normalized_filename}');
        }});
        '''

        time.sleep(2)
        driver.execute_script(download_script)
        time.sleep(5)

    if not check_exists_by_css_selector(driver, GO_TO_NEXT_IMAGE_BTN):
        break
    
    while True:
        try:
            driver.find_element_by_css_selector(GO_TO_NEXT_IMAGE_BTN).click()
            time.sleep(0.5)
        except StaleElementReferenceException:
            print('Stale element error')
            time.sleep(5)
            continue
        break



time.sleep(30)
print(' [*] Finished!')
driver.quit()
