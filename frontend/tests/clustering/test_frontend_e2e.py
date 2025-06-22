from playwright.sync_api import sync_playwright

def test_dashboard_loads_and_interactions():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:80")
        try:
            page.wait_for_selector("#ticker-select", timeout=20000)
        except Exception:
            page.screenshot(path="debug_dashboard.png")
            print(page.content())
            raise
        page.wait_for_selector("#dashboard-content", timeout=10000)
        page.wait_for_selector(".cluster-card", timeout=10000)
        # Select a different ticker if available
        options = page.query_selector_all('#ticker-select option')
        if len(options) > 1:
            second_ticker = options[1].get_attribute('value')
            page.select_option('#ticker-select', second_ticker)
            page.wait_for_selector(f'#summary-ticker:has-text("{second_ticker}")', timeout=10000)
        # Check price and technical charts
        page.wait_for_selector('#price-chart', timeout=10000)
        page.wait_for_selector('#technical-chart', timeout=10000)
        # Optionally, simulate API failure by disconnecting backend and checking error overlay (manual step)
        browser.close() 