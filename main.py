import os

from scrapers.CNNScraper import CNN_Scraper
from scrapers.WashPoScraper import WashingtonPost_Scraper
from scrapers.PoynterScraper import Poynter_Scraper
from scrapers.GuardianScraper import Guardian_Scraper
from ScraperManager import Scraper_Manager


def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


cnn_path = os.path.join(os.getcwd(), "results\\CNN")
washpo_path = os.path.join(os.getcwd(), "results\\WashingtonPost")
poynter_path = os.path.join(os.getcwd(), "results\\Poynter")
guardian_path = os.path.join(os.getcwd(), "results\\Guardian")

make_dir(cnn_path)
make_dir(washpo_path)
make_dir(poynter_path)
make_dir(guardian_path)

scrapers_dict = {
    "CNN Scraper": CNN_Scraper(cnn_path, "coronavirus measures"),
    "Washington Post Scraper": WashingtonPost_Scraper(washpo_path, "covid"),
    "Poynter Scraper": Poynter_Scraper(poynter_path),
    "Guardian Scraper": Guardian_Scraper(guardian_path),
}

manager = Scraper_Manager(scrapers_dict)
manager.run_all()
