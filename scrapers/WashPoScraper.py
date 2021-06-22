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


class WashingtonPost_Scraper(Scraper):
    timeout = 10  # should give up trying to load page after 10 seconds
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
        self.url = f"https://www.washingtonpost.com/newssearch/?query={query}&btn-search=&sort=Relevance&startat="

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
                    "Title",
                    "Text",
                    "Author",
                    "Country",
                ]
            )
        self.prev_articles.drop(
            columns=[
                column for column in self.prev_articles.columns if "Unnamed" in column
            ],
            inplace=True,
        )
        self.prev_urls = self.prev_articles["URL"].to_list()
        print(self.prev_urls)

    def _load_page(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located((By.ID, "main-content")))

    def _load_article(self, url):
        self.driver.get(url)
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located((By.ID, "fusion-app")))

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
        soup = self._get_soup(self.url + "0")
        results = soup.find("div", {"class": "pb-search-results-total"})
        return int(results.span.text.replace(",", ""))

    def _get_article(self, url):
        try:
            soup = self._get_soup(url)
        except Exception:
            return
        complete_data = True
        authors = ""
        sources = ""
        authors_list = soup.find_all(
            "span", {"class": "author-name font-bold black"}
        ) + soup.find_all(
            "span", {"class": "author-name font-bold link blue hover-blue-hover"}
        )
        for author in authors_list:
            source = re.search(r"(?<=\|).*", author.text)
            source = source.group().strip() if source else ""
            if source and author.text.find(source) > 0:
                name = author.text[: author.text.find(source) - 2]
            else:
                name = author.text

            if name:
                authors += name.strip() + ", "
            else:
                complete_data = False
            if source:
                sources += source + " "
            else:
                complete_data = False
        sources = sources.strip() if sources else "Washington Post"
        authors = authors[:-2]  # remove trailing comma
        content = ""
        for text in soup.find_all("p", {"data-el": "text"}):
            content += text.text

        article_date = ""
        try:
            article_date = re.search(
                ".*(?<=20\d\d)", soup.find("div", {"class": "display-date"}).text
            ).group()
            try:
                article_date = datetime.strptime(article_date, "%B %d, %Y")
            except ValueError:
                article_date = datetime.strptime(article_date, "%b. %d, %Y")
        except Exception:
            article_date = "NA"
            complete_data = False

        category = ""
        try:
            category = soup.find("a", {"class": "font-bold link black hover-blue"}).text
        except AttributeError:
            category = "NA"
            complete_data = False
        try:
            title = soup.find("span", {"data-qa": "headline-opinion-text"}).text
        except AttributeError:
            try:
                title = soup.find(
                    "h1", {"class": "font--headline balanced-headline pb-md undefined"}
                ).text
            except AttributeError:
                title = "NA"
                complete_data = False
        logging.info(
            f"Following data extracted: {authors} (authors), {title}, (title), {article_date} (date), {category} (category), {sources} (sources)"
        )
        article_df = pd.DataFrame(
            [
                [
                    url,
                    article_date,
                    sources,
                    category,
                    self.search_terms,
                    title,
                    content,
                    authors,
                    "NA",
                ]
            ],
            columns=self.prev_articles.columns,
        )
        self.prev_articles = self.prev_articles.append(article_df, ignore_index=True)
        self.prev_urls.append(url)
        if complete_data:
            self.data_with_tags += 1
        self.articles_scraped += 1

    def run(self):
        results = self._get_total_results()
        logging.info(f"{results} results found")

        try:
            for i in range(0, results, 10):

                soup = self._get_soup(f"{self.url}{i}")
                valid_urls = [
                    url["data-sid"]
                    for url in soup.find_all("div", {"class": "pb-feed-item ng-scope"})
                    if url["data-sid"]
                    and "covid-live-updates-us" not in url["data-sid"]
                ]
                for url in valid_urls:
                    url = "https://" + url
                    if url not in self.prev_urls and "/video/" not in url:
                        logging.info(f"Scraping: {url}")
                        self.driver.delete_all_cookies()
                        self._get_article(url)
        except Exception as e:
            logging.info(f"Failed to fully scrape articles: {repr(e)}")
        finally:
            self.prev_articles.drop(
                columns=[
                    column
                    for column in self.prev_articles.columns
                    if "Unnamed" in column
                ],
                inplace=True,
            )
            self.prev_articles.to_csv(self.path)
            run_data = f"Completed run. Scraped {self.articles_scraped} with {self.data_with_tags} fully filled out articles."
            self._update_log(run_data)
            logging.info(run_data)
            try:
                self.driver.close()
            except Exception as e:
                logging.error(f"Unable to close the chrome driver: {str(e)}")

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
    wp_scraper = WashingtonPost_Scraper(
        os.path.join(os.getcwd(), "results\\WashingtonPost"), "covid"
    )
    wp_scraper.run()
