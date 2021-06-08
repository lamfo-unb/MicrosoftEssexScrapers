from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pandas as pd
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
from webdriver_manager.chrome import ChromeDriverManager

try:
    from scraper import Scraper
except Exception:
    from scrapers.scraper import Scraper

timeout = 60

class Poynter_Scraper(Scraper):
    timeout = 60  # should give up trying to load page after 10 seconds
    data_with_tags = 0
    articles_scraped = 0

    def __init__(self, output_path: str):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--incognito")  # incognito disables cache

        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        self.driver.delete_all_cookies()

        self.url = f"https://www.poynter.org/ifcn-covid-19-misinformation/"

        self.log_path = output_path + "\\update_log.txt"
        self.path = output_path + "\\articles.csv"

        try:
            self.prev_articles = pd.read_csv(self.path)
        except FileNotFoundError:
            self.prev_articles = pd.DataFrame(
                columns=[
                  "PreviewURL", "ReportURL", "Date", "Source", "Title", "Label", "Explanation", "Country"
                ]
            )

        self.prev_urls = self.prev_articles["PreviewURL"].to_list()

    def _load_page(self, url):

        self.driver.get(url)
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located((By.ID, "primary")))

    def _get_soup(self, url):

        try:
            self._load_page(url)
        except Exception:
            logging.info("Initial load failed... reloading page")
            try:
                self._load_page(url)
            except Exception:
                logging.error(f"Secondary Load failed.... skipping: {url}")
                raise

        page = BeautifulSoup(self.driver.page_source, "html.parser")

        return page

    def _get_total_results(self):
        soup = self._get_soup(self.url)
        results = soup.find_all("a", {"class": "page-numbers"})
        total = results[-2].text
        return int(total)
    
    def _scrape_article(self, article):
        preview_url = article.find("a")["href"]  
        if preview_url in self.prev_urls:
          return
        article_info = dict.fromkeys(self.prev_articles.columns)
        title_label_info = article.find("a").text.split(":")
        label, title = title_label_info[0], "".join([s for s in title_label_info[1:]])
        date, countries = article.find("strong").text.split("|")
        source = article.find("p").text.split(": ")[1]

        
        article_soup = self._get_soup(preview_url)
        article_text = article_soup.find("div", {"class" : "post-container"})
        explanation = article_text.find("p", {"class" : "entry-content__text entry-content__text--explanation"}).text.split(":")[1]
        report_url = article_text.find("a")["href"]

        article_info["Label"] = label
        article_info["Title"] = title
        article_info["Date"] = datetime.strptime(date.strip(), "%Y/%m/%d")
        article_info["Source"] = source
        article_info["PreviewURL"] = preview_url
        article_info["ReportURL"] = report_url
        article_info["Explanation"] = explanation
        article_info["Country"] = countries

        self.prev_articles = self.prev_articles.append(pd.DataFrame.from_dict(article_info, orient="index").transpose(), ignore_index=True)
        self.articles_scraped += 1
    def run(self):
      pages = self._get_total_results()
      try:
          #for i in range(1, 4):
          for i in range(1, pages + 1):
              url = self.url + f"page/{i}/"
              soup = self._get_soup(url)
              [self._scrape_article(article) for article in soup.find_all("div", {"class" : "post-container"})]
      except Exception as e:
          logging.info(f"Failed to scrape articles: {str(e)}")
      finally:
          self.prev_articles.to_csv(self.path)

          run_data = f"Completed run. Scraped {self.articles_scraped} articles."
          self._update_log(run_data)
          logging.info(run_data)
          try:
              self.driver.close()
          except Exception as e:
              logging.error(f"Unable to close the chrome driver: {str(e)}")

    def get_name(self):
        return "Poynter Scraper"

    def _update_log(self, text):
        today = datetime.now()
        mode = "w+"
        if os.path.exists(self.log_path):
            mode = "a"
        with open(self.log_path, mode) as f:
            f.write(f"\nOn {today}: {text}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        handlers=[logging.StreamHandler()],
    )
    Poynter_scraper = Poynter_Scraper(
        os.path.join(os.getcwd(), "results\\Poynter")
    )
    Poynter_scraper.run()
