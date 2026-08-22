#!/usr/bin/env python3

import re
import sys
import shlex
import subprocess
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

COOKIE = {
    "PHPSESSID": "YOUR_PHPSESSID",
    "EPRNS": "YOUR_EPRNS",
    "ageverif_accepted": "T",
}

QUALITY_ORDER = [
    "1080-av1",
    "1080",
    "720-av1",
    "720",
    "480-av1",
    "480",
    "360",
]

ARIA_SPLIT = 16
ARIA_CONN = 16

# --------------------------------------------------

DLOAD_RE = re.compile(
    r"https://www\.eporner\.com/dload/[^\s\"'<>]+",
    re.I
)


def create_session():
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False,
        }
    )

    scraper.headers.update({
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0 Safari/537.36",
        "Referer": "https://www.eporner.com/",
    })

    for k, v in COOKIE.items():
        scraper.cookies.set(
            k,
            v,
            domain=".eporner.com"
        )

    return scraper


def get_html(session, url):
    last_error = None

    for attempt in range(5):
        try:
            r = session.get(
                url,
                timeout=30,
                allow_redirects=True
            )

            r.raise_for_status()
            return r.text

        except Exception as e:
            last_error = e
            print(f"[Retry {attempt+1}/5] {e}")

    raise last_error


def extract_dloads(html, page_url):
    dloads = set()

    dloads.update(DLOAD_RE.findall(html))

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("a", href=True):
        href = urljoin(page_url, tag["href"])

        if "/dload/" in href:
            dloads.add(href)

    return sorted(dloads)


def select_best(dloads):
    if not dloads:
        return None

    for quality in QUALITY_ORDER:
        for url in dloads:
            if quality in url.lower():
                return url

    return dloads[0]


def build_cookie_header():
    return "; ".join(
        f"{k}={v}"
        for k, v in COOKIE.items()
    )


def download_with_aria2(url):
    cookie_header = build_cookie_header()

    cmd = [
        "aria2c",

        "--continue=true",
        "--file-allocation=none",

        "--split=%d" % ARIA_SPLIT,
        "--max-connection-per-server=%d" % ARIA_CONN,

        "--min-split-size=1M",

        "--retry-wait=3",
        "--max-tries=20",

        "--timeout=60",
        "--connect-timeout=30",

        "--check-certificate=false",

        "--summary-interval=1",

        "--header=Referer: https://www.eporner.com/",
        "--header=User-Agent: Mozilla/5.0",
        f"--header=Cookie: {cookie_header}",

        url,
    ]

    print("\nLaunching aria2c:\n")
    print(
        " ".join(
            shlex.quote(x)
            for x in cmd
        )
    )
    print()

    subprocess.run(
        cmd,
        check=True
    )


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage:\n"
            f"python {sys.argv[0]} <eporner_video_url>"
        )
        sys.exit(1)

    url = sys.argv[1]

    print("[+] Creating session...")
    session = create_session()

    print("[+] Fetching page...")
    html = get_html(session, url)

    print("[+] Extracting download links...")
    dloads = extract_dloads(html, url)

    if not dloads:
        print("No download links found.")
        sys.exit(1)

    print(f"[+] Found {len(dloads)} links")

    best = select_best(dloads)

    print("\nSelected:")
    print(best)

    print("\nStarting aria2c download...\n")

    download_with_aria2(best)


if __name__ == "__main__":
    main()