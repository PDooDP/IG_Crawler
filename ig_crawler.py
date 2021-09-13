# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 22:21:59 2021

@author: Dennis
"""

# IG webcrawler

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import wget # 下載資料的模組
import json

imgs_list = []
videos_list = []

# sid紀錄對象的帳戶 id
# sid = '########' # 使用者id (手動尋找輸入)
# username = input("請輸入IG帳號: ")
# password = input("請輸入IG密碼: ")
sid = input("請輸入目標的ID: ")
PATH = '~\chromedriver.exe'
driver = webdriver.Chrome(PATH)
first = 50  # 最大可回傳50組資料(50篇)

# login_url = "https://www.instagram.com"
url = 'https://www.instagram.com/graphql/query/?query_hash=8c2a529969ee035a5063f2fc8602a0fd&variables={"id":"' + sid + '","first":' + str(first) +'}'


def login(url):
    driver.get(url)
    
    username = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "username"))
    )
    
    password = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    
    login = driver.find_element_by_xpath('//*[@id="loginForm"]/div/div[3]')
    
    username.clear()
    time.sleep(3)
    password.clear()
    time.sleep(3)
    username.send_keys("your_username")
    time.sleep(3)
    password.send_keys("your_password")
    time.sleep(5)
    login.click()
    
    search = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//*[@id="react-root"]/section/nav/div[2]/div/div/div[2]/input'))
    )
    
    # stayLogin = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div/section/div/button')
    # time.sleep(3)
    # stayLogin.click()
    

# 抓取json資料
def loadPage(url):
    driver.get(url)
    # 使用JS去抓取頁面原始碼
    SourceToJson(driver.execute_script("return document.body.innerHTML;"))


# 將HTML原始碼轉成JSON, 並儲存在page_source.json 
def SourceToJson(pageSource):
    data = pageSource.replace('<pre style="word-wrap: break-word; white-space: pre-wrap;">',"").replace('</pre>',"")

    # 寫成json檔
    fileToWrite = open("page_source.json", "w", encoding = "utf-8")
    fileToWrite.write(data)
    fileToWrite.close()

# 找出end_cursor值
def getPageInfo():
    global imgs_list, videos_list, data_dict, data_count
    data = loadJson()
    data_dict = data["data"]["user"]["edge_owner_to_timeline_media"]
    
    has_next_page = data_dict["page_info"]["has_next_page"]
    end_cursor = data_dict["page_info"]["end_cursor"]
    
    # 1. 先檢查是否有幾篇文章, 一次最多50篇
    data_count = len(data_dict["edges"])
    
    # 2. 判斷貼圖格式: 照片，影片或是群組的(一張以上)
    # j 為貼文編號順序， 布林值False代表該貼圖格式不是群組的, -1則代表只有一張貼圖
    for j in range(data_count):
        data_type = chkSourceType(j)
        if data_type == "GraphImage":
            isImg(j, False, -1)
        elif data_type == "GraphVideo":
            isVideo(j, False, -1)
        else:
            isSidecar(j)
    
    # 如果has_next_page為True, 代表有下一頁的token, 則回傳end_cursor內的值
    if has_next_page != False:
        return end_cursor

# 取得總文章數
def getTotalCount():
    data = loadJson()
    data_dict = data["data"]["user"]["edge_owner_to_timeline_media"]
    total_count = int(data_dict["count"])
    return total_count

# 開啟JSON檔
def loadJson():
    f = open("page_source.json", encoding="utf-8")
    json_data = json.load(f)
    return json_data

# 藉由__typename判斷取得的資料為GraphImage, GraphVideo, GraphSidecar
# 如判斷為GraphImage, display_url為圖片來源 (jpg)
# 如判斷為GraphVideo, video_url為影片來源 (mp4)
# 如判斷為GraphSidecar, 則是media群組, 內含多筆圖片或影片資料
# 先找出貼文內有幾筆資料, 再重新呼叫函式判斷是否為圖片還是影片
def chkSourceType(index):
    data = loadJson()
    data_dict = data["data"]["user"]["edge_owner_to_timeline_media"]
    data_type = data_dict["edges"][index]["node"]["__typename"]
    return data_type

# =================================================================================================
# index 為貼文編號順序， isSidecar: 布林值False代表該貼圖格式不是群組的, -1則代表只有一張貼圖
# 將原檔url 存進imgs_list串列中
def isVideo(index, isSidecar, i = -1):
    # 把video url存進一個list, 最後再用wget的方式下載下來
    if isSidecar != True:
        result = data_dict["edges"][index]["node"]["video_url"]
    else:
        data_sidecar = data_dict["edges"][index]["node"]["edge_sidecar_to_children"]["edges"][i]
        result = data_sidecar["node"]["video_url"]
    videos_list.append(result)
            
def isImg(index, isSidecar, i = -1):
    # 把img url存進一個list, 最後再用wget的方式下載下來
    if isSidecar != True:
        result = data_dict["edges"][index]["node"]["display_url"]
    else:
        data_sidecar = data_dict["edges"][index]["node"]["edge_sidecar_to_children"]["edges"][i]
        result = data_sidecar["node"]["display_url"]
    imgs_list.append(result)

def isSidecar(index):
    data = loadJson()
    data_dict = data["data"]["user"]["edge_owner_to_timeline_media"]
    data_sidecar = data_dict["edges"][index]["node"]["edge_sidecar_to_children"]["edges"]
    sidecar_size = len(data_sidecar)
    for i in range(sidecar_size):
        data_type = data_sidecar[i]["node"]["__typename"]
        if data_type == "GraphImage":
            isImg(index, True, i)
        elif data_type == "GraphVideo":
            isVideo(index, True, i)
            
# =================================================================================================

# 計算一共要跑幾頁
def file_loop(total_count, url):
    if (total_count % first) != 0:
        loop_count = int(total_count / first) + 1
        for i in range(loop_count):
            time.sleep(1)
            f = loadPage(url)
            after = getPageInfo()
            time.sleep(2)
            # print(after)
            if after != None:
                url = url.replace("}","") + ',"after":"' + after + '"}'
                # print(url)

# 將取得的原始URL位置保存在notepad裡
def createTxt():
    fn = sid + ".txt"
    with open(fn, 'w') as file_obj:
        for img in imgs_list:
            file_obj.write(img + "\n")
            
        for video in videos_list:
            file_obj.write(img + "\n")

def saveImages(account):
    file_path = os.path.join(account) # join是傳回檔案路徑的方式
    img_count = 0
    if os.path.exists(account):
        print("已經存在資料夾: " + account)
        files = os.listdir(account)
        img_count = len(files)
        if img_count != 0:
            img_count -= 1
        else:
            img_count = 0
    else:
        os.mkdir(file_path)
    
    for img in imgs_list:
        save_as = os.path.join(file_path, account + "_" + str(img_count) + ".jpg")
        # print(img.get_attribute("src"))
        wget.download(img, save_as)
        img_count += 1
        
    for video in videos_list:
        save_as = os.path.join(file_path, account + "_" + str(img_count) + ".mp4")
        # print(img.get_attribute("src"))
        wget.download(video, save_as)
        img_count += 1

# === 程式進入點 ===
login(url)
loadPage(url)
# total_count = getTotalCount()
file_loop(getTotalCount(), url)
createTxt() # 原始url位置
saveImages(sid) # 使用wget開始下載
print("資料抓取成功!")
# === 程式結束 ===
