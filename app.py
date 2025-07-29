import asyncio
from flask import Flask, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

async def fetch_matches():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.fancode.com/", wait_until="networkidle")

        # Wait for match cards to appear (adjust selector if needed)
        await page.wait_for_selector('div[data-testid="match-card"]', timeout=15000)

        matches = await page.evaluate('''() => {
            const cards = Array.from(document.querySelectorAll('div[data-testid="match-card"]'));
            return cards.map(card => {
                const titleEl = card.querySelector('div[class*="matchTitle"]');
                const statusEl = card.querySelector('div[class*="matchStatus"]');
                const timeEl = card.querySelector('div[class*="matchStartTime"]');

                // Try find m3u8 link in anchor tags inside card
                let m3u8 = null;
                const anchors = card.querySelectorAll('a');
                for (const a of anchors) {
                    if (a.href && a.href.endsWith('.m3u8')) {
                        m3u8 = a.href;
                        break;
                    }
                }

                return {
                    title: titleEl ? titleEl.textContent.trim() : null,
                    status: statusEl ? statusEl.textContent.trim() : null,
                    start_time: timeEl ? timeEl.textContent.trim() : null,
                    m3u8_link: m3u8
                };
            });
        }''')

        await browser.close()

        return matches


@app.route('/matches')
def matches_api():
    data = asyncio.run(fetch_matches())
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
