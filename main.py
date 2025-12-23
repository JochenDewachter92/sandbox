import os
import re
import time
import hashlib
import argparse
from urllib.parse import urlparse, unquote

import requests
from tqdm import tqdm
from playwright.sync_api import sync_playwright


def pick_largest_from_srcset(srcset: str) -> str | None:
    """
    srcset looks like: "url1 320w, url2 640w, url3 1080w"
    We pick the url with the largest width descriptor.
    """
    if not srcset:
        return None
    best_url = None
    best_w = -1
    for part in srcset.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(.+)\s+(\d+)w$", part)
        if m:
            url = m.group(1).strip()
            w = int(m.group(2))
            if w > best_w:
                best_w = w
                best_url = url
        else:
            # Sometimes srcset contains just URLs; keep last as fallback
            best_url = part.split()[0]
    return best_url


def safe_filename_from_url(url: str, fallback_ext: str = ".jpg") -> str:
    """
    Create a stable filename from the URL path; if it's messy, use a hash.
    """
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        base = os.path.basename(path)
        # Remove FB CDN tokens/odd fragments
        base = base.split("?")[0].strip()
        if base and "." in base and len(base) < 200:
            return base
    except Exception:
        pass

    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"fb_{h}{fallback_ext}"


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def scroll_and_collect_image_urls(page, max_scrolls: int, pause: float) -> list[str]:
    """
    Scrolls down the page and collects image URLs (prefers largest from srcset).
    """
    urls = set()
    last_height = 0
    stagnant_count = 0

    for i in range(max_scrolls):
        # Collect imgs currently in DOM
        imgs = page.query_selector_all("img")
        for img in imgs:
            src = img.get_attribute("src") or ""
            srcset = img.get_attribute("srcset") or ""

            best = pick_largest_from_srcset(srcset) or src
            if not best:
                continue

            # Filter: Facebook images are typically on fbcdn / scontent
            if ("fbcdn" in best) or ("scontent" in best):
                urls.add(best)

        # Scroll
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause)

        # Detect if scrolling still loads more content
        height = page.evaluate("document.body.scrollHeight")
        if height == last_height:
            stagnant_count += 1
        else:
            stagnant_count = 0
            last_height = height

        # If no more new content loads after a few tries, stop early
        if stagnant_count >= 5:
            break

    return sorted(urls)


def download_with_browser_cookies(context, urls: list[str], out_dir: str, timeout: int = 30):
    """
    Downloads using requests, but injects cookies from the Playwright context
    so it works for member-only content (when direct CDN requires auth).
    """
    ensure_dir(out_dir)

    # Grab cookies from the browser context
    cookies = context.cookies()
    jar = requests.cookies.RequestsCookieJar()
    for c in cookies:
        jar.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path"))

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    session = requests.Session()
    session.cookies = jar
    session.headers.update(headers)

    seen = set(os.listdir(out_dir))

    for url in tqdm(urls, desc="Downloading"):
        filename = safe_filename_from_url(url)
        # Avoid overwriting; if exists, skip
        if filename in seen:
            continue

        path = os.path.join(out_dir, filename)

        try:
            r = session.get(url, stream=True, timeout=timeout)
            r.raise_for_status()

            # Try to infer extension if missing
            if "." not in os.path.basename(path):
                ct = r.headers.get("Content-Type", "")
                ext = ".jpg"
                if "png" in ct:
                    ext = ".png"
                elif "webp" in ct:
                    ext = ".webp"
                path += ext

            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)

            seen.add(os.path.basename(path))

        except Exception as e:
            # Keep going; FB links can occasionally 403/expire
            print(f"\n[WARN] Failed: {url}\n       {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Download photos from a Facebook page/group (member-only) using Playwright."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Target Facebook URL. Use the Photos page if possible (examples below)."
    )
    parser.add_argument(
        "--out",
        default="fb_photos",
        help="Output folder (default: fb_photos)"
    )
    parser.add_argument(
        "--profile",
        default="fb_profile",
        help="Persistent browser profile folder (stores your login)."
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=200,
        help="Max scroll steps (default: 200). Increase for large albums."
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=1.2,
        help="Pause between scrolls in seconds (default: 1.2)."
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open browser so you can log in, then close. Run again without --login to scrape."
    )
    args = parser.parse_args()

    ensure_dir(args.profile)
    ensure_dir(args.out)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=args.profile,
            headless=False,  # keep visible; Facebook often blocks headless
            viewport={"width": 1280, "height": 900},
        )
        page = browser.new_page()
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

        if args.login:
            print("\nLogin mode:")
            print("1) Log into Facebook in the opened browser window.")
            print("2) When you are fully logged in, close the browser window.")
            print("3) Then run the script again WITHOUT --login.\n")
            try:
                # Wait until user closes
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                browser.close()
            return

        # Navigate to target
        page.goto(args.url, wait_until="domcontentloaded")
        time.sleep(3)

        print("\nScrolling and collecting image URLs...")
        urls = scroll_and_collect_image_urls(page, args.max_scrolls, args.pause)
        print(f"Collected {len(urls)} image URLs.")

        # Download
        download_with_browser_cookies(browser, urls, args.out)

        browser.close()
        print(f"\nDone. Saved into: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
