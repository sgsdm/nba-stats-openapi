import asyncio
from collections import deque
from urllib.parse import urlparse
from typing import Any
import json

from playwright.async_api import async_playwright, Browser, Route, Request, TimeoutError


async def get_api_request(route: Route, request: Request, returned_data: dict[str, Any]) -> None:
    if request.url.startswith("https://stats.nba.com/stats"):
        url = urlparse(request.url)
        returned_data["endpoint"] = url.path
        response = await route.fetch()
        json = await response.json()
        try:
            result = json.get("resultSet", None)
            if result is None:
                result = json.get("resultSets", None)
                if isinstance(result, list):
                    for result_set in result:
                        row_set = result_set["rowSet"]
                        if isinstance(row_set, list):
                            result_set["rowSet"] = row_set[0:3] # first 3 elements only
                else:
                    row_set = result["rowSet"]
                    result["rowSet"] = row_set[0:3]
            else:
                row_set = result["rowSet"]
                result["rowSet"] = row_set[0:3]
        except KeyError as e:
            print(e)
            pass
        returned_data["example"] = json
    
    await route.continue_()


async def main() -> None:
    crawl_links: deque[str] = deque(["/stats/players/traditional"])
    processed: dict[str, dict[str, Any]] = {}
    done: set[str] = set()
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=False)
        while crawl_links:
            link = crawl_links.pop()
            if link in processed.keys():
                continue
            print(f"Processing endpoint {link}")
            page = await browser.new_page()
            processed[link] = {}
            try:
                await page.route(
                    "**/*.{png,jpg,jpeg,svg}", lambda route: route.abort()
                )
                await page.route("**/*", lambda route, request: get_api_request(route, request, processed[link]))

                await page.goto("https://www.nba.com" + link)
                await page.wait_for_selector('table[class^="Crom_table"]')

                nav_list = await page.query_selector(".nba-stats-quick-nav")
                assert nav_list is not None
                found_links = [
                    await item.get_attribute("href")
                    for item in await nav_list.query_selector_all("a")
                ]
                crawl_links.extend(filter(None, found_links))

                header = await page.query_selector('table[class^="Crom_table"] > thead > tr')
                assert header is not None
                descriptions: dict[str, dict[str, str | None]] = {}
                for item in await header.query_selector_all("th"):
                    field_name = await item.get_attribute("field")
                    if field_name is None:
                        continue
                    description = await item.get_attribute("title")
                    shorthand: str = await item.inner_text()
                    descriptions[field_name] = {
                        "description": description,
                        "shorthand": shorthand
                    }
                done.add(link)
                processed[link]["description"] = descriptions
                with open("dump.json", "w") as json_file:
                    json.dump(processed, json_file, indent=2)
                
            except TimeoutError as e:
                print(e)
                pass

            await page.close()

        await browser.close()



asyncio.run(main())
