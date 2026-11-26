"""Optional real Chromium smoke test. Run while the local backend is running.
Uses a direct extension-page URL to exercise the same code as the side panel.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright, expect

EXT = Path(__file__).resolve().parents[1] / 'extension'
with TemporaryDirectory() as profile, sync_playwright() as p:
    opts = dict(headless=True, args=[f'--disable-extensions-except={EXT}', f'--load-extension={EXT}', '--no-sandbox'])
    if os.getenv('CHROMIUM_PATH'):
        opts['executable_path'] = os.environ['CHROMIUM_PATH']
    else:
        opts['channel'] = 'chromium'
    context = p.chromium.launch_persistent_context(profile, **opts)
    try:
        worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker', timeout=15000)
        extension_id = worker.url.split('/')[2]
        panel = context.new_page()
        panel.goto(f'chrome-extension://{extension_id}/panel.html')
        panel.set_viewport_size({'width':420,'height':900})
        panel.locator('#goal').fill('Book a bus ticket')
        panel.locator('#run').click()
        expect(panel.locator('#status')).to_have_text('Complete',timeout=15000)
        bus = next(t for t in context.pages if t.url.endswith('/demo/bus'))
        expect(bus.locator('#from')).to_have_value('Bengaluru')
        expect(bus.locator('#to')).to_have_value('Mysuru')
        expect(bus.locator('#result')).to_be_visible()
        expect(panel.locator('#simple')).to_contain_text('Available buses')
        panel.locator('[data-intent="bill"]').click()
        expect(panel.locator('#status')).to_have_text('Complete',timeout=15000)
        bill = next(t for t in context.pages if t.url.endswith('/demo/bill'))
        expect(bill.locator('#consumer-id')).to_have_value('DEMO-1042')
        expect(bill.locator('#result')).to_be_visible()
        expect(bill.get_by_role('button',name='Pay now (disabled)')).to_be_disabled()
        panel.locator('[data-intent="scheme"]').click()
        expect(panel.locator('#status')).to_have_text('Complete',timeout=15000)
        scheme = next(t for t in context.pages if t.url.endswith('/demo/scheme'))
        expect(scheme.locator('#result')).to_be_visible()
        panel.locator('[data-intent="compare"]').click()
        expect(panel.locator('#status')).to_have_text('Complete',timeout=15000)
        expect(panel.locator('#comparison')).to_contain_text('₹280')
        expect(panel.locator('#comparison')).to_contain_text('₹320')
        expect(panel.locator('#comparison a')).to_have_count(2)
        if os.getenv('SAHAJ_SCREENSHOT'):
            panel.screenshot(path=os.environ['SAHAJ_SCREENSHOT'],full_page=True)
        panel.locator('#goal').fill('unknown request')
        panel.locator('#run').click()
        expect(panel.locator('#status')).to_have_text('Stopped',timeout=15000)
        print('PASS: real Chromium extension page, navigation, input, clicks, read-only cards, all four flows, comparison and unsupported-goal handling.')
    finally:
        context.close()
