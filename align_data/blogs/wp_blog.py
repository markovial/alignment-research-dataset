from datetime import datetime, timezone
from calendar import c
from dataclasses import dataclass, field
import logging
import feedparser

from align_data.common import utils
from align_data.common.alignment_dataset import AlignmentDataset, DataEntry

from typing import List

logger = logging.getLogger(__name__)

@dataclass
class WordpressBlog(AlignmentDataset):
    url: str
    strip: List = field(default_factory=lambda: [])
    summary_key = 'summary'
    done_key = 'paged_url'

    def setup(self):
        """
        url: URL of the blog
        strip: list of regexes to strip from the HTML
        """
        super().setup()
        self.feed_url = self.url + "/feed"
        self.cleaner = utils.HtmlCleaner(self.strip)
        self.name = utils.url_to_filename(self.url)

    def get_item_key(self, item):
        return item

    def get_page_count(self):
        """ 
        Instead of creating a list of urls up to 2000, 
        which makes tqdm think that there are 2000 items 
        to process, we'll find the last valid page number 
        and create a list of urls up to that page number.
        We use exponential search to find the last valid page number.
        """
        last_title = [None]  # We'll use a list so that we can modify it inside the inner function

        def is_valid_page(i):
            paged_url = f"{self.feed_url}?paged={i + 1}"
            d = feedparser.parse(paged_url)
            if ("feed" in d) and ("title" in d["feed"]) and d["feed"]["title"] != last_title[0]:
                last_title[0] = d["feed"]["title"]
                return True
            else:
                return False

        bound = 1
        while is_valid_page(bound):
            bound *= 2  # Exponentially increase the bound
            if bound > 8000:
                raise Exception("Something is wrong, we shouldn't be getting this many pages")

        # Now we know the page number lies between bound/2 and bound, perform binary search
        lower_bound = bound // 2
        upper_bound = bound
        while upper_bound - lower_bound > 1:
            mid = (lower_bound + upper_bound) // 2
            if is_valid_page(mid):
                lower_bound = mid
            else:
                upper_bound = mid
        return lower_bound + 1

    @property
    def items_list(self):
        return [f"{self.feed_url}?paged={page + 1}" for page in range(self.get_page_count())]

    @staticmethod
    def _get_published_date(item):
        date_published = item.get('published')
        if not date_published:
            return ''
        dt = datetime.strptime(date_published, '%a, %d %b %Y %H:%M:%S %z').astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch_entries(self):
        for paged_url in self.unprocessed_items():
            logger.info(f"Fetching {paged_url}")
            d = feedparser.parse(paged_url)

            for entry in d["entries"]:
                content_text = self.cleaner.clean(entry["content"][0]["value"])
                text = entry["title"] + "\n\n" + content_text

                new_entry = DataEntry({
                    "text": text,
                    "url": entry['link'],
                    "title": text.split("\n")[0],
                    "source": self.name,
                    "source_type": "blog",
                    "date_published": self._get_published_date(entry),
                    "paged_url": paged_url,
                    "authors": [e['name'] for e in entry.get('authors', [])],
                })
                new_entry.add_id()

                yield new_entry
