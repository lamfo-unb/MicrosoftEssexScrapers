import os

from scrapers.CNNScraper import CNN_Scraper
from scrapers.WashPoScraper import WashingtonPost_Scraper
from scrapers.PoynterScraper import Poynter_Scraper
from ScraperManager import Scraper_Manager

scrapers_dict = {
    "CNN Scraper": CNN_Scraper(
        os.path.join(os.getcwd(), "results\\CNN"), "coronavirus measures"
    ),
    "Washington Post Scraper": WashingtonPost_Scraper(
        os.path.join(os.getcwd(), "results\\WashingtonPost"), "covid"
    ),
    "Poynter Scraper": Poynter_Scraper(os.path.join(os.getcwd(), "results\\Poynter")),
}

manager = Scraper_Manager(scrapers_dict)
manager.run_all()
