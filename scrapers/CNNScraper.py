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


class Article:
    def __init__(self, title, date, url, content, categories, search_terms, author):
        if type(title) is not str:
            raise ValueError("The name passed is not a string")
        self.title = title

        if type(date) is not str:
            try:
                self.date = str(date)
            except ValueError:
                self.date = None
        self.date = date

        if type(url) is not str:
            raise ValueError("Please pass the URL as a string")
        self.url = url

        if type(content) is not str:
            raise ValueError("Please pass the content of the article as a string")
        self.content = content
        self.categories = categories
        self.search_terms = search_terms
        self.author = author

    def __str__(self):
        return (
            "Article Title: "
            + self.title
            + ", Posted On: "
            + self.date
            + ", At: "
            + self.url
        )

    def __eq__(self, obj):
        return (
            isinstance(obj, Article) and self.title == obj.title and obj.url == self.url
        )

    def to_txt(self, path: str):
        filename = path + re.sub(r"[\s?\"\\/\*\:\<\>|]", "", self.title) + ".txt"
        with open(filename, "wb") as file:
            file.write(self.__str__().encode("utf8"))
            file.write(("\n" + self.content).encode("utf8"))

    def to_df(self):
        return pd.DataFrame(
            {
                "URL": [self.url],
                "Date": [self.date],
                "Source": ["CNN"],
                "Category": [self.categories],
                "Search": [self.search_terms],
                "Title": [self.title],
                "Text": [self.content],
                "Author": [self.author],
                "Country": ["USA"],
            }
        )


class CNN_Scraper(Scraper):
    timeout = 60  # should give up trying to load page after 10 seconds
    data_with_tags = 0
    articles_scraped = 0

    def __init__(self, output_path: str, search_terms: str):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--incognito")  # incognito disables cache

        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        self.driver.delete_all_cookies()

        self.search_terms = search_terms
        query = search_terms.replace(" ", "%20")
        self.url = f"https://edition.cnn.com/search/?size=10&q={query}&page=1"

        self.log_path = output_path + "\\update_log.txt"
        self.path = output_path + "\\articles.csv"

        try:
            self.prev_articles = pd.read_csv(self.path)
        except FileNotFoundError:
            self.prev_articles = pd.DataFrame(
                columns=[
                    "URL",
                    "Date",
                    "Source",
                    "Category",
                    "Search",
                    "Text",
                    "Author",
                    "Country",
                ]
            )
        self.prev_urls = self.prev_articles["URL"].to_list()

    def _load_CNN_page(self, url):

        self.driver.get(url)
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located((By.ID, "segment")))

    def _get_CNN_soup(self, url):

        try:
            self._load_CNN_page(url)
        except Exception:
            logging.info("Initial load failed... reloading page")
            try:
                self._load_CNN_page(url)
            except Exception:
                logging.error(f"Secondary Load failed.... skipping: {url}")
                raise

        page = BeautifulSoup(self.driver.page_source, "html.parser")

        return page

    def _get_total_results(self):
        CNN_soup = self._get_CNN_soup(self.url)

        results = CNN_soup.find("div", {"class": "cnn-search__results-count"})
        total = re.search(r"\d+(?= for)", results.text)
        return int(total.group())

    def run(self):
        try:
            total_results = self._get_total_results()
        except Exception:
            logging.info("Total results didn't show.. trying again")
            total_results = self._get_total_results()

        try:
            self._scrape_articles(total_results)
        except Exception as e:
            logging.info(f"Failed to scrape articles: {str(e)}")
        finally:
            self.prev_articles.to_csv(self.path)

            run_data = f"Completed run. Scraped {self.articles_scraped} with {self.data_with_tags} fully filled out articles."
            self._update_log(run_data)
            logging.info(run_data)
            try:
                self.driver.close()
            except Exception as e:
                logging.error(f"Unable to close the chrome driver: {str(e)}")

    def _scrape_articles(self, total_results):  # TODO add timeout
        pagenum = 1

        while (pagenum * 10) <= int(total_results):
            url = (
                "https://edition.cnn.com/search/?size=10&q=coronavirus%20measures&page="
                + str(pagenum)
                + "&from="
                + str(10 * (pagenum - 1))
            )
            logging.info("Moving to next page:")
            logging.info(url)
            try:
                CNN_soup = self._get_CNN_soup(url)
            except Exception as e:
                logging.error(f"Ran into problem {str(e)}")
                logging.info("Moving to next page:")
                pagenum += 1
                continue
            articles = CNN_soup.find_all(
                "div", {"class": "cnn-search__result cnn-search__result--article"}
            )

            for article in articles:
                self._create_article(article)

            pagenum += 1

    def _create_article(self, article):
        title = article.find("h3", {"class": "cnn-search__result-headline"})
        article_url = "https:" + title.find_all("a", href=True)[0]["href"]
        if (
            "live-news" in article_url
            or "/health/" in article_url
            or article_url in self.prev_urls
        ):
            return
        content = article.find("div", {"class": "cnn-search__result-body"})
        try:
            article_soup = self._get_CNN_soup(article_url)
            logging.info("Getting text body")
            article_class = article_soup.find("body")
            logging.info("Finding Div")
            article_class = article_class.find(
                "div", {"class": "pg-right-rail-tall pg-wrapper"}
            )
            logging.info("Finding Rail")
            article_class = article_class.find(
                "article", {"pg-rail-tall pg-rail--align-right"}
            )
            logging.info("Extracting metadata")
            topic = article_class.find("meta", {"itemprop": "isPartOf"})["content"]
            author = article_class.find("meta", {"itemprop": "author"})["content"]
            date = article_class.find("meta", {"itemprop": "datePublished"})["content"]
            self.data_with_tags += 1

        except (AttributeError, TypeError) as e:
            logging.error(f"Doesn't contain metadata: {str(e)}")
            topic, author, date = None, None, None
        except Exception as e:
            logging.error(f"Failed to get article because of {str(e)}")
            return

        update = Article(
            title.text.lstrip(),
            date,
            article_url,
            content.text,
            topic,
            "coronavirus measures",
            author,
        )

        self.prev_articles = self.prev_articles.append(
            update.to_df(), ignore_index=True
        )
        self.prev_urls.append(article_url)
        self.articles_scraped += 1

    def get_name(self):
        return "CNN Scraper"

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
    CNN_scraper = CNN_Scraper(
        os.path.join(os.getcwd(), "results\\CNN"), "coronavirus measures"
    )
    CNN_scraper.run()
