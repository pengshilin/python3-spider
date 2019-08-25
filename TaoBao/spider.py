#!/usr/bin/env python 
# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
from TaoBao.config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL,port=27017)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser,10)

def search():
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))     #显式等待输入框10s内加载
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))    #显示等待搜索按钮
        )
        input.send_keys(KEYWORLD)   #搜索框输入关键字
        submit.click()  #点击搜索按钮
        total = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))   #等待加载页数
        get_products()
        return total
    except TimeoutException:
        return search()     #超时就重新运行

def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))    #等待页码输入框加载
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))    #页码提交
        )
        input.clear()   #清除当前页的内容
        input.send_keys(page_number)    #传入页码
        submit.click()  #点击提交
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))    #判断执行后的页码是否等于我们传入的页码
        get_products()
    except TimeoutException:
        next_page(page_number)

def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))  #获取宝贝
    html = browser.page_source  #page_source获取网页的源代码
    doc = pq(html)      #用PyQuery解析网页源代码
    items = doc('#mainsrp-itemlist .items .item').items()   #获取所有宝贝信息
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),    #图片链接
            'price': item.find('.price').text(),            #价格
            'deal': item.find('.deal-cnt').text()[:-3],     #销量
            'title': item.find('.title').text(),            #标题
            'shop': item.find('.shop').text(),              #店铺
            'location': item.find('.location').text()       #产地
        }
        print(product)
        save_to_mongo(product)                              #保存

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储成功',result)
    except Exception:
        print('存储失败',result)



def main():
    try:
        total = search()[0].text
        total = int(re.compile('(\d+)').search(total).group(1))     #这里total是共 100 页，返回100
        for i in range(2, total + 1):
            next_page(i)
    except Exception:
        print('出错了')
    finally:
        browser.close()

if __name__ == '__main__':
    main()
