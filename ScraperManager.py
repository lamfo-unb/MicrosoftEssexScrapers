import logging

try:
    from scraper import Scraper
except Exception:
    from scrapers.scraper import Scraper


class Scraper_Manager:
    """
    A class used to manage scrappers and logging

    Atributes
    ---------
    scrapers : dict
        a dictionary containing key value pairs of scraper names (str)
        and their respective scraper objects (Scraper)

    Methods
    -------
    run_all()
        runs all the scrapers and generates a log file
    """

    def __init__(self, scrapers={}):
        """
        Parameters
        ----------
        scrapers : dict
            a dictionary containing key value pairs of scraper names (str)
            and their respective scraper objects (Scraper)

        """
        self.scrapers = scrapers

        # setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
            datefmt="%m-%d %H:%M",
            handlers=[logging.FileHandler("scrapers.log"), logging.StreamHandler()],
        )

    def run_all(self):
        """Runs all the scrapers stored in the scrapers dict and generates a log file"""
        logging.info("Starting Program")
        for scraper_name, scraper in self.scrapers.items():
            try:
                logging.debug(f"Starting: {scraper_name}")
                scraper.run()
                logging.debug(f"Finishing: {scraper_name}")
            except Exception:
                logging.exception(f"{scraper_name} failed because of: ")
        logging.info("Finished Program")
        logging.shutdown()


if __name__ == "__main__":

    class TestScraper(Scraper):
        def run(self):
            print("Test")

    manager = Scraper_Manager({"Test": TestScraper()})
    manager.run_all()
