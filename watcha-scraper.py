# -*- coding: utf-8 -*-
import sys
import requests
import base64
import json
import logging
import os
import scrapy
import json
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import timeit

import logging

class JsonWriterPipeline(object):
    def __init__(self,fileName, folderName):
        self.fileName = fileName
        self.folderName = folderName

    @classmethod
    def from_crawler(cls, crawler):
        fileName = getattr(crawler.spider, "fileName")
        folderName = getattr(crawler.spider, "folderName")

        return cls(fileName,folderName)

    def open_spider(self, spider):
        self.file = open('{}/{}_review.json'.format(self.folderName, self.fileName), 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        # return item


class reviewCrawl(scrapy.Spider):
    name = "watchaReview"

    start_urls = ["https://api.watcha.com/api/contents/changeValue/comments?default_version=20&filter=all&order=popular&page=1&size=20&vendor_string=frograms"]

    tableName = ""

    custom_settings = {
        'LOG_LEVEL': logging.WARNING,#'INFO',
        'ITEM_PIPELINES': {'__main__.JsonWriterPipeline': 1}, # Used for pipeline 1
    }

    def start_requests(self):
        URL = self.start_urls[0].replace("changeValue",self.movieCode)
        self.fileName = self.movieCode
        self.folderName = self.folderName
        # for url in self.start_urls:
        yield scrapy.Request(url=URL,
                            headers = {
                                # 'Referer': "https://watcha.com/ko-KR/contents/{}/comments".format(self.movieCode),
                                'x-watcha-client' : 'watcha-WebApp',
                                'x-watcha-client-language' : 'ko',
                                'x-watcha-client-region' : 'KR',
                                'x-watcha-client-version' : "1.0.0",
                                },
                            cookies = {'_s_guit':self.userKey},
                                    callback=self.parse)

    def parse(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for i in jsonresponse['result']['result']:
            yield i

        next_page = jsonresponse['result']['next_uri']
        if next_page is not None:
            yield response.follow(next_page,
                                    headers = {
                                    # 'Referer': "https://watcha.com/ko-KR/contents/{}/comments".format(self.movieCode),
                                    'x-watcha-client' : 'watcha-WebApp',
                                    'x-watcha-client-language' : 'ko',
                                    'x-watcha-client-region' : 'KR',
                                    'x-watcha-client-version' : "1.0.0",
                                    },
                                    callback=self.parse)





def getMovieCode(movieName):
    #
    # 영화 검색화면에서 첫번째 영화의 코드를 가져온다.
    #

    # 영화 이름이 검색되지않으면 None return
    try:
        SEARCH_URL = "https://watcha.com/ko-KR/search?"
        params = {
                "query" : movieName,
            }
        resp = requests.get(SEARCH_URL, params = params)
        soup = BeautifulSoup(resp.content, "html.parser")

        # soup.find("ul", class_="css-1uosu8c-VisualUl-StyledHorizontalUl-StyledHorizontalUlWithContentPosterList").li.find("div", class_="css-2fzriy-ContentInfo").find("div", class_="e1m1t8xe1").text

        searchRaw = soup.find("ul", class_="css-1uosu8c-VisualUl-StyledHorizontalUl-StyledHorizontalUlWithContentPosterList")
        searchResult = []
        for idx,li in enumerate(searchRaw.find_all("li")):
            print("{}. {}".format(idx+1, " || ".join([ i.text for i in li.find("div", class_="css-2fzriy-ContentInfo").find_all("div")])))
            searchResult.append(li.a['href'].split("/")[-1])
        selectIdx = input("Enter index: ")

        movieCode = searchResult[int(selectIdx)-1]
        return movieCode
    except:
        print("getMovieCode error")
        sys.exit(1)


def getMovieName(movieCode):
    try:
        # SEARCH_URL = "https://watcha.com/ko-KR/search?"
        CONTENT_URL = "https://watcha.com/ko-KR/contents/{}".format(movieCode)
        resp = requests.get(CONTENT_URL)
        soup = BeautifulSoup(resp.content, "html.parser")
        name = soup.find("div", class_ = "css-13h49w0-PaneInner").h1.text # 모멘텀
        year = soup.find("div", class_ = "css-13h49w0-PaneInner").div.text[:4] # 2015
        movieName = "{}({})".format(name, year)
        return movieName
    except:
        print("getMovieName error")
        sys.exit(1)

def main():
    folderName = "review"
    try:
        if not(os.path.isdir("{}".format(folderName))):
            os.makedirs(os.path.join("{}".format(folderName)))
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("Failed to create directory!!!!!")
            raise


    BASE_DIR = os.getcwd()
    f = open(BASE_DIR+"/userInfo.txt", 'r')
    id, pw = [v[:-1] for v in f.readlines()]
    f.close()
    flag, keyword = sys.argv[1].split("=")

    if flag[1:]=="name":
        movieCode = getMovieCode(keyword)
    else:
        movieCode = keyword

    movieName = getMovieName(movieCode)

    # sys.exit(0)

    userKey, headers = getUserKey(id, pw)

    process = CrawlerProcess({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    })
    process.crawl(reviewCrawl, userKey=userKey, headers=headers, movieCode=movieCode, fileName=movieName, folderName=folderName)
    process.start()

    # sys.exit(0)



def getUserKey(id, pw):

    URL = "https://api.watcha.com/api/sessions"

    datas = {
        "email" : id,
        "password" : pw
    }


    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
        'x-watcha-client' : 'watcha-WebApp',
        'x-watcha-client-language' : 'ko',
        'x-watcha-client-region' : 'KR',
        'x-watcha-client-version' : "1.0.0"
    }


    session = requests.Session()
    resp = session.post(URL, headers = headers, data = datas)
    sessionCookies = session.cookies.get_dict()
    userKey = sessionCookies["_s_guit"]


    return userKey, headers


if __name__=='__main__':
    start = timeit.default_timer()

    main()

    stop = timeit.default_timer()
    print("소요 시간: {}분 {}초".format(int(stop-start)//60, int(stop-start)%60))
