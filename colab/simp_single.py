import re
import sys
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin

if len(sys.argv) < 2:
    print(f"Usage: python {sys.argv[0]} <url>")
    sys.exit(1)

URL = sys.argv[1]

VIDEO_RE = re.compile(
    r"https://www\.eporner\.com/video-[^/]+/[^/?#]+/?",
    re.I
)

DLOAD_RE = re.compile(
    r"https://www\.eporner\.com/dload/[^\s\"'<>]+",
    re.I
)


def create_scraper():
    return cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False,
        }
    )


def process_url(url):
    scraper = create_scraper()

    found_videos = set()
    found_dloads = set()

    try:
        r = scraper.get(url, timeout=20)
        r.raise_for_status()

        html = r.text

        found_videos.update(VIDEO_RE.findall(html))
        found_dloads.update(DLOAD_RE.findall(html))

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all("a", href=True):
            link = urljoin(url, tag["href"])

            if VIDEO_RE.match(link):
                found_videos.add(link)

            if "/dload/" in link:
                found_dloads.add(link)

        return sorted(found_videos), sorted(found_dloads)

    except Exception as e:
        print(f"[ERROR] {e}")
        return [], []


videos, dloads = process_url(URL)

best = None

# Preference order
preferences = [
    "1080-av1",
    "1080",
    "720-av1",
    "720",
    "480-av1",
    "480",
]

for quality in preferences:
    for d in dloads:
        if quality in d.lower():
            best = d
            break
    if best:
        break

if best:
    print("http://127.0.0.1:8989/" + best)
else:
    print("No suitable download link found")