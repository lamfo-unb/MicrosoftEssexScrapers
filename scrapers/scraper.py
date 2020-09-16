from abc import ABC, abstractmethod


class Scraper(ABC):
    """
    The Scraper abstract class serves as a frame work for the scraping scripts.
    Each Scraper has a run method that runs the code necessary for it to perform its task.
    """

    @abstractmethod
    def run(self):
        """Executes the code for the scraper"""
        pass
