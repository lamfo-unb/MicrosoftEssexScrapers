import time
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen as uReq
import json
import pandas as pd
import logging
import os

try:
    from scraper import Scraper
except Exception:
    from scrapers.scraper import Scraper


class Guardian_Scraper(Scraper):
    def __init__(self, output_path: str):
        self.path = f"{output_path}\\articles.csv"

    def run(self):
        cookies = dict(name="jerry", password="888")

        URL = "https://www.theguardian.com/world/coronavirus-outbreak/all"
        page = requests.get(URL, cookies=cookies)

        soup = BeautifulSoup(page.content, "html.parser")

        links = []
        titles = []

        base = []
        URL = "https://www.theguardian.com/world/coronavirus-outbreak/all"
        page = requests.get(URL, cookies=cookies)
        soup = BeautifulSoup(page.content, "html.parser")
        containers3 = ["a"]

        i = 2
        linkar = []
        while len(containers3) != 0 and len(linkar) < 11761:
            URL = "https://www.theguardian.com/world/coronavirus-outbreak?page=" + str(
                i
            )
            page = requests.get(URL, cookies=cookies)
            soup = BeautifulSoup(page.content, "html.parser")
            containers3 = soup.findAll("div", {"class": "fc-item__container"})
            for j in containers3:
                zz = j.find("a", {"class": "fc-item__link"})
                linkar.append(zz.text)
            i = i + 1

        # 662 seconds (11 minutes)
        linkar = pd.DataFrame(linkar)
        linkar["Label"] = "TRUE"
        linkar = linkar.rename(index={"0": "Title"})

        linkar.columns = ["Title", "Label"]

        linkar.to_csv(self.path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        handlers=[logging.StreamHandler()],
    )
    guardian_scraper = Guardian_Scraper(os.path.join(os.getcwd(), "results\\Guardian"))
    guardian_scraper.run()
