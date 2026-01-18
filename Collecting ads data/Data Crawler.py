#!/usr/bin/env python3
# Data_Crawler.py - cloudscraper + BeautifulSoup version
import os
import csv
import time
import shutil
import tempfile
import re
from datetime import date, timedelta, datetime
from queue import Queue
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed

import io
import logging
from logging.handlers import RotatingFileHandler

import numpy as np
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from google.cloud import bigquery
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse, parse_qs, unquote
import glob

# ---------------------------
# Config
# ---------------------------
BASE_DIR = os.path.abspath(".")
ADS_DATA_DIR = os.path.join(BASE_DIR, "ads_data")
NUM_WORKER = 16
BATCH_SAVE_SIZE = 100
REQUEST_TIMEOUT = 15  # seconds

# ---------------------------
# Logging setup
# ---------------------------
os.makedirs(ADS_DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(ADS_DATA_DIR, "ads_scraper.log")
with open(LOG_FILE, "w", encoding="utf-8"):
    pass
logger = logging.getLogger("DataCrawler")
logger.setLevel(logging.INFO)
# Rotating file handler
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ---------------------------
# Utilities: cloudscraper session with retries
# ---------------------------
def create_session():
    logger.info("Creating cloudscraper session")
    s = cloudscraper.create_scraper()
    return s

def get_with_retry(session, url, max_attempts=5, timeout=REQUEST_TIMEOUT):
    """GET with retry and logging. Logs attempt, status code, elapsed time and exceptions."""
    for attempt in range(1, max_attempts + 1):
        start_ts = time.time()
        try:
            resp = session.get(url, timeout=timeout)
            elapsed = time.time() - start_ts
            status = resp.status_code
            # logger.info("GET %s attempt=%d status=%s elapsed=%.2fs", url, attempt, status, elapsed)
            if resp.status_code == 200:
                return resp
            else:
                # treat non-200 as retryable for some codes
                if resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning("Retryable status %s for %s (attempt %d)", status, url, attempt)
                    time.sleep(1 * attempt)
                    continue
                else:
                    # non-retryable status -> return response (caller can inspect)
                    return resp
        except Exception as e:
            elapsed = time.time() - start_ts
            logger.exception("GET %s attempt=%d failed after %.2fs: %s", url, attempt, elapsed, e)
            if attempt == max_attempts:
                logger.error("Max attempts reached for %s, raising exception", url)
                raise
            time.sleep(0.5 * attempt)
    raise Exception("Failed to GET url: " + url)

# ---------------------------
# HTML parsing helpers
# ---------------------------
def soup_from_url(url):
    start = time.time()
    resp = get_with_retry(url)
    elapsed = time.time() - start
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # logger.info("Parsed HTML for %s (%.2fs)", url, elapsed)
        return soup, resp
    except Exception as e:
        logger.exception("Failed to parse HTML for %s: %s", url, e)
        raise

def text_or_none(el):
    if not el:
        return None
    return el.get_text(strip=True)

def parse_date_from_element(elem):
    # element may have aria-label "dd/mm/YYYY" or text in various formats
    if not elem:
        return None
    val = elem.get("aria-label") or elem.get_text(strip=True)
    val = val.strip()
    # try dd/mm/YYYY
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except Exception:
            pass
    # try to find dd/mm/YYYY in string
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", val)
    if m:
        try:
            return datetime.strptime(m.group(1), "%d/%m/%Y").date()
        except:
            try:
                return datetime.strptime(m.group(1), "%d/%m/%y").date()
            except:
                pass
    return None

def extract_ads_id_from_link(link):
    # previous logic: last part - number (maybe "pr123456")
    try:
        # try to find last continuous digits in the URL
        m = re.search(r"(\d+)(?:\D*$)", link)
        if m:
            return int(m.group(1))
    except:
        pass
    return None

# ---------------------------
# Scrape links (list pages)
# ---------------------------
def get_max_page_from_list_soup(soup):
    try:
        pag = soup.find("div", class_="re__pagination-group")
        if pag is None:
            return 1
        items = pag.find_all(recursive=False)
        # find near-last visible number
        texts = [x.get_text(strip=True) for x in pag.find_all()]
        # attempt to find numeric items
        nums = [int(re.sub(r"\.", "", t)) for t in texts if re.sub(r"\.", "", t).isdigit()]
        if nums:
            return max(nums)
    except Exception as e:
        logger.exception("Error finding max page: %s", e)
    return 1

def scrape_links_from_base_phase1(base_url_template, start_date, end_date, max_page, existed_ads_ids_sorted=None):
    all_links = []
    flag = existed_ads_ids_sorted is not None

    for i in range(1, max_page):
        url = base_url_template.format(i=i)
        try:
            soup, resp = soup_from_url(url)
        except Exception as e:
            logger.warning("Failed to fetch page %s: %s", url, e)
            continue

        product_list = soup.find(id="product-lists-web")
        if not product_list:
            # sometimes listing structure different; try common card selectors
            product_list = soup.select_one(".product-listing") or soup
        cards = product_list.select(".js__card-full-web")[:50]  # take up to 50
        if not cards:
            # alternative selector
            cards = product_list.select(".re__card--item")[:50]

        for card in cards:
            date_elem = card.select_one("span.re__card-published-info-published-at")

            label = card.find("div", class_="label--v1")
            if label is None:
                return all_links

            ngay_gia_han = parse_date_from_element(date_elem)
            if not ngay_gia_han:
                # fallback: try time tag or small text
                date_elem2 = card.find("time") or card.select_one(".card__time")
                ngay_gia_han = parse_date_from_element(date_elem2)

            if not ngay_gia_han:
                # cannot determine date -> skip
                continue


            if ngay_gia_han > end_date or ngay_gia_han < start_date:
                continue

            # get link
            a = card.find("a", href=True)
            if not a:
                continue
            link = a["href"]
            if not link.startswith("http"):
                link = "https://batdongsan.com.vn" + link

            ads_id = extract_ads_id_from_link(link)
            if flag and ads_id is not None:
                # check with bisect logic; simple membership test (list is small)
                # use binary search:
                import bisect
                idx = bisect.bisect_left(existed_ads_ids_sorted, ads_id)
                if idx < len(existed_ads_ids_sorted) and existed_ads_ids_sorted[idx] == ads_id:
                    # already exists -> skip
                    continue
            all_links.append((link, ngay_gia_han))

    # deduplicate
    all_links = list(set(all_links))
    logger.info("scrape_links_from_base -> found %d links", len(all_links))
    return all_links

def scrape_links_from_base_phase2(base_url_template, start_page, start_date, end_date, max_page, existed_ads_ids_sorted=None):
    all_links = []
    flag = existed_ads_ids_sorted is not None

    for i in range(max(1, start_page - 2), max_page + 1):
        url = base_url_template.format(i=i)
        try:
            soup, resp = soup_from_url(url)
        except Exception as e:
            logger.warning("Failed to fetch page %s: %s", url, e)
            continue

        product_list = soup.find(id="product-lists-web")
        if not product_list:
            # sometimes listing structure different; try common card selectors
            product_list = soup.select_one(".product-listing") or soup
        cards = product_list.select(".js__card-full-web")[:50]  # take up to 50
        if not cards:
            # alternative selector
            cards = product_list.select(".re__card--item")[:50]

        for card in cards:
            date_elem = card.select_one("span.re__card-published-info-published-at")
            ngay_gia_han = parse_date_from_element(date_elem)
            if not ngay_gia_han:
                # fallback: try time tag or small text
                date_elem2 = card.find("time") or card.select_one(".card__time")
                ngay_gia_han = parse_date_from_element(date_elem2)

            if not ngay_gia_han:
                # cannot determine date -> skip
                continue

            if ngay_gia_han > end_date:
                # newer than end_date, skip
                continue
            if ngay_gia_han < start_date:
                # older than start_date -> stop scanning further pages and log the current page
                logger.info("scrape_links_from_base -> reached older date %s < %s at page %d, stopping.",
                            ngay_gia_han.isoformat(), start_date.isoformat(), i)
                return all_links


            # get link
            a = card.find("a", href=True)
            if not a:
                continue
            link = a["href"]
            if not link.startswith("http"):
                link = "https://batdongsan.com.vn" + link

            ads_id = extract_ads_id_from_link(link)
            if flag and ads_id is not None:
                # check with bisect logic; simple membership test (list is small)
                # use binary search:
                import bisect
                idx = bisect.bisect_left(existed_ads_ids_sorted, ads_id)
                if idx < len(existed_ads_ids_sorted) and existed_ads_ids_sorted[idx] == ads_id:
                    # already exists -> skip
                    continue
            all_links.append((link, ngay_gia_han))

    # deduplicate
    all_links = list(set(all_links))
    logger.info("scrape_links_from_base -> found %d links", len(all_links))
    return all_links

# ---------------------------
# Scrape details for a single ad page
# ---------------------------
def parse_ad_page(url, resp_text=None):
    try:
        if resp_text is None:
            # soup, resp = soup_from_url(url)
            raise
        else:
            soup = BeautifulSoup(resp_text, "html.parser")
        ad_data = {}

        # Ngày gia hạn: may be absent on detail page; keep from link list
        # Mã tin from URL
        ads_id = extract_ads_id_from_link(url)
        if ads_id:
            ad_data["Mã tin"] = str(ads_id)

        # Config items (title/value)
        try:
            config_items = soup.select(".js__pr-config-item")
            for item in config_items:
                title_el = item.select_one(".title")
                value_el = item.select_one(".value")
                if title_el and value_el:
                    ad_data[title_el.get_text(strip=True)] = value_el.get_text(strip=True)
        except Exception:
            logger.exception("Error parsing config items for %s", url)

        # Breadcrumbs for Loại quảng cáo, Loại BĐS, Tỉnh, Quận, Địa chỉ 1
        try:
            bc = soup.select_one(".js__ob-breadcrumb")
            if bc:
                a_tags = bc.find_all("a")
                if len(a_tags) >= 1:
                    ad_data["Loại quảng cáo"] = a_tags[0].get_text(strip=True)
                    ad_data["Loại BĐS"] = a_tags[0].get("title") or a_tags[0].get_text(strip=True)
                if len(a_tags) >= 2:
                    ad_data["Tỉnh, thành phố"] = a_tags[1].get_text(strip=True)
                if len(a_tags) >= 3:
                    ad_data["Quận"] = a_tags[2].get_text(strip=True)
                if len(a_tags) >= 4:
                    ad_data["Địa chỉ 1"] = a_tags[3].get_text(strip=True)
        except Exception:
            logger.exception("Error parsing breadcrumbs for %s", url)

        # Address full from specific selector
        try:
            addr_el = soup.find(class_="js__pr-address")
            if addr_el:
                ad_data["Địa chỉ 2"] = addr_el.get_text(" ", strip=True)
        except Exception:
            logger.exception("Error parsing address for %s", url)

        # Product features
        try:
            titles = soup.select(".re__pr-specs-content-item-title")
            values = soup.select(".re__pr-specs-content-item-value")
            for t, v in zip(titles, values):
                ad_data[t.get_text(strip=True)] = v.get_text(strip=True)
        except Exception:
            logger.exception("Error parsing product features for %s", url)

        # Project link and name - try a few heuristics
        try:
            # tìm container chính (an toàn nếu tên class thay đổi nhẹ)
            container = soup.find(class_="re__project-card-info") or soup.find(class_="re__ldp-project-info")
            if not container:
                ad_data["Link dự án"] = None
                ad_data["Tên dự án"] = None

            else:
                # tên dự án
                title_tag = container.find("div", class_="re__project-title")
                ad_data["Tên dự án"] = title_tag.get_text(strip=True) if title_tag else None

                # link dự án
                ad_data["Link dự án"] = None
                avatar = container.find("div", class_="re__section-avatar")
                if avatar:
                    a = avatar.find("a", href=True)
                    if a:
                        ad_data["Link dự án"] = a["href"]
        except Exception:
            logger.exception("Error parsing project info for %s", url)

        # Map coordinates: try multiple strategies
        try:
            coords = None
            # find by class name re__pr-map or re__map
            map_block = soup.select_one(".re__pr-map, .re__map")

            if map_block:
                # search for img with data-src
                img = map_block.find("img", attrs={"data-src": True})
                if img:
                    ds = img["data-src"]
                    # try to extract lat,lng after '=' or 'center='
                    m = re.search(r"center=([\d\.-]+),([\d\.-]+)", ds)
                    if m:
                        coords = f"{m.group(1)},{m.group(2)}"
                    else:
                        # try last =...&key
                        m2 = re.search(r"=([\d\.-]+),([\d\.-]+)&", ds)
                        if m2:
                            coords = f"{m2.group(1)},{m2.group(2)}"
                        else:
                            # if ds has lat,lng somewhere
                            m3 = re.search(r"([\d\.-]+),([\d\.-]+)", ds)
                            if m3:
                                coords = f"{m3.group(1)},{m3.group(2)}"
                # iframe?
                if not coords:
                    iframe = map_block.find("iframe", class_="lazyload")
                    if iframe:
                        # ưu tiên data-src (lazyload), fallback sang src
                        url = iframe.get("data-src") or iframe.get("src")
                        if not url:
                            coords = ""

                        # decode %xx và &amp; -> &
                        url = unquote(url)

                        # 1) cố gắng lấy param q từ query string: ?q=lat,lng
                        parsed = urlparse(url)
                        qs = parse_qs(parsed.query)
                        q_vals = qs.get("q")
                        if q_vals:
                            q0 = q_vals[0]
                            m = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", q0)
                            if m:
                                coords = f"{m.group(1)},{m.group(2)}"

                        # 2) một số URL chứa @lat,lng,zoom (ví dụ @12.34,56.78,17z)
                        m = re.search(r"@(-?\d+\.\d+),\s*(-?\d+\.\d+)", url)
                        if m:
                            coords = f"{m.group(1)},{m.group(2)}"

                        # 3) fallback: tìm bất kỳ cặp số thập phân liền nhau "lat,lng" trong toàn bộ URL
                        m = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", url)
                        if m:
                            coords = f"{m.group(1)},{m.group(2)}"

            ad_data["Tọa độ"] = coords or ""
        except Exception:
            logger.exception("Error parsing map coords for %s", url)
            ad_data["Tọa độ"] = ""

        # Published / dates: try to find elements with date info
        try:
            # small tag or span with 'Ngày đăng' or similar
            labels = soup.select(".re__pr-publish-info, .pr-publish")
            if labels:
                # attempt to find date tokens
                txt = " ".join([l.get_text(" ", strip=True) for l in labels])
                m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", txt)
                if m:
                    ad_data["Ngày đăng"] = m.group(1)
        except Exception:
            logger.exception("Error parsing publish dates for %s", url)

        # # Mức giá / Diện tích often in same header area; try common selectors
        # try:
        #     price_el = soup.select_one(".re__pr-title .price, .re__pr-price, .product-price")
        #     if price_el:
        #         ad_data["Mức giá"] = price_el.get_text(" ", strip=True)
        #     area_el = soup.find(text=re.compile(r"m²|m2|m²", re.I))
        #     # area_el may return a text node; ignore if not meaningful
        # except Exception:
        #     logger.exception("Error parsing price/area for %s", url)

        return ad_data
    except Exception as e:
        logger.exception("[ERROR parse_ad_page] %s -> %s", url, e)
        return None

# ---------------------------
# Worker to collect ads data concurrently
# ---------------------------
def collect_ads_data(links, num_worker=NUM_WORKER):
    # prepare worker dirs
    os.makedirs(ADS_DATA_DIR, exist_ok=True)
    for i in range(num_worker):
        os.makedirs(os.path.join(ADS_DATA_DIR, f"worker{i}_data"), exist_ok=True)

    # resume logic: count existing files to compute start index
    last_index = 0
    for i in range(num_worker):
        d = os.path.join(ADS_DATA_DIR, f"worker{i}_data")
        if os.path.exists(d):
            last_index += len([f for f in os.listdir(d) if f.endswith(".xlsx")])

    start_index = last_index * BATCH_SAVE_SIZE
    links_to_process = links[start_index:]

    def worker_func(worker_id, sub_links):
        batch = []

        # create session
        session = create_session()
        logger.info(f"Starting worker {worker_id}")

        # get last batch index and save as new batch
        saved_batches = max(0, len([f for f in os.listdir(os.path.join(ADS_DATA_DIR, f"worker{worker_id}_data")) if f.endswith(".xlsx")]))

        out_dir = os.path.join(ADS_DATA_DIR, f"worker{worker_id}_data")
        for idx, (url, ngay_gia_han) in enumerate(sub_links):
            try:
                # logger.info("Worker %d fetching %s", worker_id, url)
                # fetch page and parse
                resp = get_with_retry(session, url)
                ad = parse_ad_page(url, resp_text=resp.text)
                if not ad:
                    logger.warning("Worker %d: parse returned no data for %s", worker_id, url)
                    continue
                ad["Ngày gia hạn"] = ngay_gia_han
                # ensure Mã tin exists: fallback to parse from URL
                if "Mã tin" not in ad or not ad["Mã tin"]:
                    mid = extract_ads_id_from_link(url)
                    if mid:
                        ad["Mã tin"] = str(mid)
                batch.append(ad)

                # save when batch size reached
                if len(batch) >= BATCH_SAVE_SIZE:
                    df = pd.DataFrame(batch)
                    filename = os.path.join(out_dir, f"ads_data_batch{saved_batches + 1}.xlsx")
                    df.to_excel(filename, index=False)
                    # logger.info("Worker %d saved batch %s", worker_id, filename)
                    saved_batches += 1
                    batch = []
            except Exception as e:
                logger.exception("[WARN worker %d] %s -> %s", worker_id, url, e)
                continue

        # save remaining
        if batch:
            df = pd.DataFrame(batch)
            filename = os.path.join(out_dir, f"ads_data_batch{saved_batches + 1}.xlsx")
            df.to_excel(filename, index=False)
            # logger.info("Worker %d saved final batch %s", worker_id, filename)

    # distribute links among workers evenly
    chunks = [[] for _ in range(num_worker)]
    for i, item in enumerate(links_to_process):
        chunks[i % num_worker].append(item)

    threads = []
    for i in range(num_worker):
        t = Thread(target=worker_func, args=(i, chunks[i]))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

# ---------------------------
# Data processing & BigQuery
# ---------------------------
def data_processing(df1: pd.DataFrame):
    df = df1.copy()

    def convert_to_float(text, unit=" m²"):
        try:
            if pd.isna(text):
                return None
            text = str(text)
            # Remove thousands separator and normalize decimals
            text = text.replace(".", "").replace(",", ".")
            text = text.replace(unit, "").strip()
            return float(text)
        except:
            return None

    if "Diện tích" in df.columns:
        df["Diện tích"] = df["Diện tích"].apply(lambda x: convert_to_float(x, unit="m²") if isinstance(x, str) else convert_to_float(x))
    # handle numeric fields that may not exist
    if "Số phòng ngủ" in df.columns:
        df["Số phòng ngủ"] = df["Số phòng ngủ"].astype(str).str.replace(" phòng", "", regex=False).replace({"nan": None})
        df["Số phòng ngủ"] = pd.to_numeric(df["Số phòng ngủ"], errors="coerce").astype("Int64")
    if "Số phòng tắm, vệ sinh" in df.columns:
        df["Số phòng tắm, vệ sinh"] = df["Số phòng tắm, vệ sinh"].astype(str).str.replace(" phòng", "", regex=False).replace({"nan": None})
        df["Số phòng tắm, vệ sinh"] = pd.to_numeric(df["Số phòng tắm, vệ sinh"], errors="coerce").astype("Int64")
    if "Số toilet" in df.columns:
        df["Số toilet"] = df["Số toilet"].astype(str).str.replace(" phòng", "", regex=False).replace({"nan": None})
        df["Số toilet"] = pd.to_numeric(df["Số toilet"], errors="coerce").astype("Int64")

    # Dates
    for col in ["Ngày đăng", "Ngày gia hạn", "Ngày hết hạn"]:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            except:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    # Loại BĐS cleanup
    if "Loại BĐS" in df.columns:
        df["Loại BĐS"] = df["Loại BĐS"].astype(str).str.replace("Bán ", "", regex=False)
        df["Loại BĐS"] = df["Loại BĐS"].astype(str).str.replace("Cho thuê ", "", regex=False)
        df["Loại BĐS"] = df["Loại BĐS"].astype(str).str.replace("Cho thuê, sang nhượng ", "", regex=False)
        df["Loại BĐS"] = df["Loại BĐS"].astype(str).str.replace(" tại Việt Nam", "", regex=False)

    # Địa chỉ 1 processing: split "xxx tại yyy"
    if "Địa chỉ 1" in df.columns:
        def process_khu_vuc(text):
            try:
                return text.split(" tại ")[1]
            except:
                return None
        df["Địa chỉ 1"] = df["Địa chỉ 1"].apply(lambda x: process_khu_vuc(x) if isinstance(x, str) else None)

    # Địa chỉ 2 processing: extract Phường/Xã/Thị trấn
    if "Địa chỉ 2" in df.columns:
        pattern = re.compile(r'(Phường|P\.?\s*\d+|P\b|Xã|Xa|Thị trấn|TT)', re.I)

        def extract_phuong(text):
            if not isinstance(text, str):
                return None
            parts = [p.strip() for p in text.split(",")]
            for p in parts:
                if pattern.search(p):
                    return p  # trả về phần đã strip
            return None

        df["Phường/Xã/Thị trấn"] = df["Địa chỉ 2"].apply(lambda x: extract_phuong(x) if isinstance(x, str) else None)

    # Mức giá parsing (attempt)
    if "Mức giá" in df.columns:
        def parse_price(val):
            try:
                if pd.isna(val):
                    return np.nan
                text = str(val)
                parts = text.split()
                if not parts:
                    return np.nan
                first = parts[0].replace(".", "").replace(",", ".")
                try:
                    first_num = float(first)
                except:
                    if first.lower().startswith("thỏa"):
                        return np.nan
                    return np.nan
                second = parts[1] if len(parts) > 1 else ""
                if second in ("tỷ", "tỷ/tháng"):
                    return first_num * 1e9
                if second in ("triệu", "triệu/tháng"):
                    return first_num * 1e6
                if second == "triệu/m²" and "Diện tích" in df.columns:
                    return first_num * 1e6  # handled later per row
                if second == "nghìn/m²":
                    return first_num * 1e3
                if second in ("nghìn", "nghìn/tháng"):
                    return first_num * 1e3
                if second == "tỷ/m²":
                    return first_num * 1e9
                return first_num
            except:
                return np.nan

        df["Mức giá"] = df["Mức giá"].apply(parse_price)

    # Tọa độ split
    if "Tọa độ" in df.columns:
        def split_coords(x):
            try:
                if not x or x == "":
                    return (None, None)
                if isinstance(x, str):
                    parts = x.split(",")
                    if len(parts) >= 2:
                        return (float(parts[0]), float(parts[1]))
                return (None, None)
            except:
                return (None, None)
        coords = df["Tọa độ"].apply(lambda x: split_coords(x))
        df["Tọa độ x"] = coords.apply(lambda t: t[0])
        df["Tọa độ y"] = coords.apply(lambda t: t[1])
        df = df.drop(columns=["Tọa độ"])

    # Rename columns similar to original
    column_mapping = {
        "Loại quảng cáo": "Loai_quang_cao", "Loại BĐS": "Loai_BDS", "Tỉnh, thành phố": "Tinh_thanh_pho",
        "Quận": "Quan", "Địa chỉ 1": "Dia_chi_1", "Diện tích": "Dien_tich", "Mức giá": "Muc_gia",
        "Hướng nhà": "Huong_nha", "Số phòng ngủ": "So_phong_ngu", "Pháp lý": "Phap_ly", "Nội thất": "Noi_that",
        "Link dự án": "Link_du_an", "Tên dự án": "Ten_du_an", "Ngày đăng": "Ngay_dang", "Ngày hết hạn": "Ngay_het_han",
        "Loại tin": "Loai_tin", "Mã tin": "Ma_tin", "Hướng ban công": "Huong_ban_cong", "Số toilet": "So_toilet",
        "Đường vào": "Duong_vao", "Số tầng": "So_tang", "Mặt tiền": "Mat_tien", "Số phòng tắm, vệ sinh": "So_phong_tam_ve_sinh",
        "Tọa độ x": "Toa_do_x", "Tọa độ y": "Toa_do_y", "Ngày gia hạn": "Ngay_gia_han", "Tiện ích": "Tien_ich",
        "Thời gian dự kiến vào ở": "Thoi_gian_du_kien_vao_o", "Mức giá điện": "Muc_gia_dien", "Mức giá internet": "Muc_gia_internet",
        "Mức giá nước": "Muc_gia_nuoc"
    }
    df.rename(columns=column_mapping, inplace=True)

    # convert object columns to str
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)

    # drop rows missing essential fields
    needed = ["Ma_tin", "Loai_tin", "Ngay_dang", "Ngay_het_han", "Loai_quang_cao", "Loai_BDS", "Tinh_thanh_pho",
              "Quan", "Dien_tich", "Khu_vuc"]
    existing_needed = [c for c in needed if c in df.columns]
    if existing_needed:
        df.dropna(subset=existing_needed, inplace=True)

    df = df.replace(['nan', "None", 'NA', 'N/A', 'null'], np.nan).infer_objects(copy=False)
    # log dataframe info to logger
    buf = io.StringIO()
    df.info(buf=buf)
    logger.info("Dataframe info:\n%s", buf.getvalue())
    return df

def push_data_to_bigquery(data_dir=ADS_DATA_DIR,
                          project_id="real-estate-project-445516", dataset_id="real_estate_data",
                          table_id="ads_data", num_worker=NUM_WORKER):
    # concat excel files from workers
    df_all = pd.DataFrame()
    for i in range(num_worker):
        worker_dir = os.path.join(data_dir, f"worker{i}_data")
        if not os.path.exists(worker_dir):
            continue
        files = [f for f in os.listdir(worker_dir) if f.endswith(".xlsx")]
        for f in files:
            path = os.path.join(worker_dir, f)
            try:
                df_temp = pd.read_excel(path, engine="openpyxl", dtype=str)
                df_all = pd.concat([df_all, df_temp], ignore_index=True)
            except Exception as e:
                logger.exception("[WARN] Failed to read %s: %s", path, e)
                continue

    if df_all.empty:
        logger.info("No data to push to BigQuery.")
        return

    df_proc = data_processing(df_all)

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    try:
        job = client.load_table_from_dataframe(df_proc, table_ref, job_config=job_config)
        job.result()
        logger.info("Successfully pushed data to %s", table_ref)
    except Exception as e:
        logger.exception("Error pushing to BigQuery: %s", e)

# ---------------------------
# Helper: get max date in BigQuery
# ---------------------------
def get_max_ngay_gia_han(project_id="real-estate-project-445516", dataset_id="real_estate_data", table_id="ads_data",
                         column_name="Ngay_gia_han"):
    client = bigquery.Client()
    query = f"SELECT MAX({column_name}) AS max_ngay_gia_han FROM `{project_id}.{dataset_id}.{table_id}`"
    try:
        query_job = client.query(query)
        result = query_job.result()
        for row in result:
            return row.max_ngay_gia_han
    except Exception as e:
        logger.exception("[WARN get_max_ngay_gia_han] %s", e)
        return None

# ---------------------------
# Wrapper: decide start page using binary search (approx)
# ---------------------------
def find_start_page(base_url_template, end_date, low, high):
    # binary search on pages by checking dates
    while low < high:
        mid = (low + high) // 2
        url = base_url_template.format(i=mid)
        try:
            soup, _ = soup_from_url(url)
        except Exception:
            return low
        cards = (soup.find(id="product-lists-web") or soup).select(".js__card-full-web")[:20]
        if not cards:
            cards = (soup.find(id="product-lists-web") or soup).select(".re__card--item")[:20]
        # if no cards, break
        if not cards:
            return low
        # check published date of first card
        date_elem = cards[0].select_one("span.re__card-published-info-published-at")
        ngay_gia_han = parse_date_from_element(date_elem)
        if ngay_gia_han is None:
            # fallback check last card
            date_elem2 = cards[-1].select_one("span.re__card-published-info-published-at")
            ngay_gia_han = parse_date_from_element(date_elem2)
        if ngay_gia_han is None:
            return low
        if ngay_gia_han <= end_date:
            high = mid
        else:
            low = mid + 1
    return low


def get_existed_ads_ids(project_id="real-estate-project-445516", dataset_id="real_estate_data", table_id="ads_data"):
    client = bigquery.Client()

    # Construct the SQL query
    query = f"""
        SELECT DISTINCT Ma_tin
        FROM `{project_id}.{dataset_id}.{table_id}`
    """

    try:
        # Run the query
        query_job = client.query(query)
        result = query_job.result()

        # Extract all values
        ads_ids = [row.Ma_tin for row in result]
        return ads_ids
    except Exception as e:
        print(f"Error: {e}")
        return None

def determine_start_date():
    max_ngay_gia_han = get_max_ngay_gia_han()

    if max_ngay_gia_han:
        # Add 1 day to the max date
        start_date = max_ngay_gia_han + timedelta(days=1)
    else:
        # Raise an error if the table is empty
        raise Exception("The table is empty")

    return start_date

# ---------------------------
# scrape_links_wrapper
# ---------------------------
def scrape_links_wrapper():
    base_urls = [
        "https://batdongsan.com.vn/nha-dat-ban/p{i}",
        "https://batdongsan.com.vn/nha-dat-cho-thue/p{i}"
    ]

    # determine start/end dates (example uses yesterday)
    # start_date = determine_start_date()
    start_date = date.today() - timedelta(days=1)
    end_date = date.today() - timedelta(days=1)

    # get existed ads ids (optional)
    existed_ads_ids = None
    # existed_ads_ids = get_existed_ads_ids()  # uncomment if desired

    all_scraped_links = []

    for base in base_urls:
        # fetch page1 to get max page
        try:
            soup, _ = soup_from_url(base.format(i=1))
            max_page = get_max_page_from_list_soup(soup)
        except Exception:
            max_page = 1

        # phase 1
        links = scrape_links_from_base_phase1(base, start_date, end_date, max_page,
                                       existed_ads_ids_sorted=None if existed_ads_ids is None else [int(x) for x in existed_ads_ids])
        all_scraped_links.extend(links)

        # phase 2
        start_page = find_start_page(base, end_date, 1, max_page)
        logger.info("For base %s, determined start_page=%d", base, start_page)
        links = scrape_links_from_base_phase2(base, start_page, start_date, end_date, max_page,
                                       existed_ads_ids_sorted=None if existed_ads_ids is None else [int(x) for x in existed_ads_ids])
        all_scraped_links.extend(links)

    # save to CSV
    os.makedirs(ADS_DATA_DIR, exist_ok=True)
    scraped_csv = os.path.join(ADS_DATA_DIR, "scraped_links.csv")
    if os.path.exists(scraped_csv):
        os.remove(scraped_csv)
    with open(scraped_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for link, ngay in all_scraped_links:
            writer.writerow([link, ngay.isoformat()])
    logger.info("Number of URLs: %d", len(all_scraped_links))
    return all_scraped_links

# ---------------------------
# collect_ads_data_wrapper
# ---------------------------
def collect_ads_data_wrapper(num_worker=NUM_WORKER):
    scraped_csv = os.path.join(ADS_DATA_DIR, "scraped_links test.csv")
    if not os.path.exists(scraped_csv):
        logger.error("scraped_links.csv not found. Run scrape_links_wrapper() first.")
        return
    all_scraped_links = []
    with open(scraped_csv, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                all_scraped_links.append((row[0], datetime.strptime(row[1], "%Y-%m-%d").date()))
            except:
                continue
    collect_ads_data(all_scraped_links, num_worker=num_worker)

def clear_previous_data():
    """
    Xóa chỉ các thư mục worker*_data trong ADS_DATA_DIR (không xóa file/dir khác),
    rồi tái tạo các thư mục worker theo NUM_WORKER.
    """
    pattern = os.path.join(ADS_DATA_DIR, "worker*_data")
    for path in glob.glob(pattern):
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                # cố gắng sửa quyền rồi thử lại (đơn giản, không phức tạp)
                try:
                    for root, dirs, files in os.walk(path):
                        for nm in files:
                            fp = os.path.join(root, nm)
                            try:
                                os.chmod(fp, stat.S_IWRITE)
                            except Exception:
                                pass
                        for nm in dirs:
                            dp = os.path.join(root, nm)
                            try:
                                os.chmod(dp, stat.S_IWRITE)
                            except Exception:
                                pass
                    os.chmod(path, stat.S_IWRITE)
                    shutil.rmtree(path)
                except Exception as e2:
                    # log nếu có logger, nếu không thì in
                    try:
                        logger.exception("Failed to remove %s: %s", path, e2)
                    except Exception:
                        print(f"Failed to remove {path}: {e2}")

    # recreate base dir and worker dirs (leave other items untouched)
    os.makedirs(ADS_DATA_DIR, exist_ok=True)
    for i in range(NUM_WORKER):
        os.makedirs(os.path.join(ADS_DATA_DIR, f"worker{i}_data"), exist_ok=True)
# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    clear_previous_data()
    # scrape_links_wrapper()
    collect_ads_data_wrapper()
    # push_data_to_bigquery()  # uncomment to push (ensure GOOGLE_APPLICATION_CREDENTIALS set)
