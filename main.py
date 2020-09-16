import os

from scrapers.CNNScraper import CNN_Scraper
from ScraperManager import Scraper_Manager

scrapers_dict = {
    "CNN Scraper" : CNN_Scraper(os.path.join(os.getcwd(), "results\\CNN"), "coronavirus measures")
}

manager = Scraper_Manager(scrapers_dict)
manager.run_all()