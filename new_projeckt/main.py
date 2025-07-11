import asyncio
import time


import aiohttp
from fake_useragent import UserAgent

from dotenv import load_dotenv
import os


load_dotenv()

token = os.getenv("GITHUB_TOKEN")


repos_lst = []
ua = UserAgent()


async def check_rate_limit(session):
    url = "https://api.github.com/rate_limit"
    headers = {
        "Authorization": f"token {token}",
        "User-Agent": ua.random
    }

    async with session.get(url=url, headers=headers) as resp:
        headers = resp.headers
        remaining = int(headers.get("X-RateLimit-Remaining", 0))
        reset = int(headers.get("X-RateLimit-Reset", 0)) - int(time.time())
        return remaining, reset


async def get_page(session, page, per_page=30):
    url = "https://api.github.com/search/repositories"
    params = {
            "q": "language:python stars:>500",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
    headers = {'user-agent': ua.random,
                   "Authorization": f"token {token}",
                   'Accept': 'application/vnd.github+json'
                   }

    async with session.get(url=url, headers=headers, params=params) as response:
        if response.status == 403:
            remaining, reset = await check_rate_limit(session)
            await asyncio.sleep(reset + 1)

            return await get_page(session, page, per_page)

        data = await response.json()
        return data.get("items", [])


async def get_all_pages(page=1, per_page=30):
    all_repos = []


    async with aiohttp.ClientSession() as session:
        while True:
            remaining, reset = await check_rate_limit(session)
            if remaining <= 1:
                await asyncio.sleep(reset + 1)

            items = await get_page(session, page)

            if not items:
                print("[DONE]")
                break

            all_repos.extend(items)
            page += 1

            await asyncio.sleep(1)

        return all_repos


async def main():
    tasks = [
        get_all_pages()
    ]
    repos = await asyncio.gather(*tasks)

    return repos

if __name__ == "__main__":
    all_repos = asyncio.run(main())


    for r in all_repos:
        for s in r:
            print(f"{s['full_name']} - ⭐ {s['stargazers_count']}")