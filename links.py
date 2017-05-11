from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import urllib
from datetime import date
import re
import time
import datetime
import sys
curDate=date.today() 
curDateStr = str(curDate.year)+"."+str(curDate.month)+"."+str(curDate.day)
logFile = open("Log_File_"+curDateStr+".txt","w+")


print("Script started on "+curDateStr)

driver = webdriver.Chrome()    
"""
driver = webdriver.PhantomJS() 
"""
#driver.maximize_window()
start_url = 'https://s.1688.com/selloffer/offer_search.htm?keywords=%E8%A4%D9%A4%B5%E6&n=y&spm=a260k.635.1998096057.d1'
print("Store URL: "+start_url)

driver.get(start_url)

WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH,"//*[@id=\"s-module-overlay\"]/div[2]/div/div[2]/em[4]")))
#driver.save_screenshot("home-screen.png")
print("Clicking on Offer Dialog box")
driver.find_element_by_xpath("//*[@id=\"s-module-overlay\"]/div[2]/div/div[2]/em[4]").click()

time.sleep(5)
change_page = True
totalProductCnt = 0
while (change_page):
    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH,"//*[@id=\"sw-mid-result\"]/div[1]")))
      
    for curProdInd in range(1,61): 
        #curProdInd += 1
        totalProductCnt += 1
        prourl = driver.find_element_by_xpath("//*[@id=\"offer"+str(curProdInd)+"\"]").get_attribute("t-offer-id")
        prourl = "https://detail.1688.com/offer/"+str(prourl)+".html?tracelog=p4p"
        print("Count: "+ str(totalProductCnt) + " : " + prourl)
        logFile.write("\n"+prourl)
        
        if(curProdInd==20):
            driver.execute_script("curWindowHt = document.body.scrollHeight; window.scrollTo(0, 4000);")
            print("clicking on scroll bar")
            time.sleep(10)
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH,"//*[@id=\"offer"+str(curProdInd)+"\"]")))
        if(curProdInd==40):
            driver.execute_script("curWindowHt = document.body.scrollHeight; window.scrollTo(0, 8000);")
            print("clicking on scroll bar")
            time.sleep(10)
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH,"//*[@id=\"offer"+str(curProdInd)+"\"]")))
        if(curProdInd==60):
            #driver.execute_script("curWindowHt = document.body.scrollHeight; window.scrollTo(0, 12000);")
            print("clicking on scroll bar")
            
        
    
    logFile.flush()
    #time.sleep(5)
    """change_page = False
    """
    
    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH,"//*[@id=\"fui_widget_4\"]/span/a[10]")))
    next_page = driver.find_elements_by_class_name("fui-next")[0]       
    curretPageFlag = next_page.get_attribute("class")  
    
    if curretPageFlag =='fui-next fui-next-disabled':
        change_page = False
    else:
        print("clicking on 'Next' Page")
        driver.execute_script("curWindowHt = document.body.scrollHeight; window.scrollTo(0, 0);")
        next_page.click()
        time.sleep(10)
logFile.close()
print("Script completed on "+curDateStr)