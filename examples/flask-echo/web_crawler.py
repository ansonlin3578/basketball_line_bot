from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time
from datetime import datetime, timedelta
import asyncio
import pandas as pd


async def get_html(url, selector, sleep=5, retries=3):
    html = None
    for i in range(1, retries+1):
        time.sleep(sleep * i)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    executable_path=r'C:\Users\User\AppData\Local\ms-playwright\chromium-1041\chrome-win\chrome.exe'
                )
                page = await browser.new_page()
                await page.goto(url)
                print(await page.title())
                # inner_html is scraping the certain piece of the page
                html = await page.inner_html(selector)
        except PlaywrightTimeout:
            print(f"Timeout error on {url}")
            continue
        else:
            break
    return html


def parse_html(box_score):
    html = asyncio.run(get_html(box_score, "#content .content_grid"))
    soup = BeautifulSoup(html, features="html.parser")
    [s.decompose() for s in soup.select("tr.over_head")]
    [s.decompose() for s in soup.select("tr.thead")]
    return soup


def read_line_score(soup):
    line_score = pd.read_html(str(soup), attrs={"id": "line_score"})[0]
    cols = list(line_score.columns)
    cols[0] = "team"
    cols[-1] = "total"
    line_score.columns = cols
    line_score = line_score[["team", "total"]]
    return line_score


def game_today():
    # time long difference bwtween taiwan & USA
    curr_time = datetime.now() - timedelta(days=2)
    curr_year, curr_month, curr_day = curr_time.year, curr_time.month, curr_time.day
    print("year : ", curr_year)
    print("month : ", curr_month)
    print("date : ", curr_day)

    url = "https://www.basketball-reference.com/boxscores/index.fcgi?" + \
        f"month={curr_month}&day={curr_day}&year={curr_year}"
    html_test = asyncio.run(get_html(url, "#content .game_summaries"))
    # print(html_test)
    soup = BeautifulSoup(html_test, features="html.parser")
    links = soup.find_all("a")
    hrefs = [link.get("href") for link in links]
    box_scores = [
        link for link in hrefs if link and ("boxscores" in link) and
        ("pbp" not in link) and ("shot-chart" not in link)
        ]
    box_scores = [i for n, i in enumerate(box_scores) if i not in box_scores[:n]]
    box_scores = [f"https://www.basketball-reference.com{link}" for link in box_scores]

    result_str = ""
    for box_score in box_scores:
        soup = parse_html(box_score)
        line_score = read_line_score(soup)
        line_score - line_score.set_axis(['Visit', 'Home'], axis="index")
        game_string = line_score.to_string()
        result_str = f"{result_str}\n###############\n" + game_string
    return result_str
