from html import escape

OFFERS = {
    'a': {'provider': 'Demo Transit', 'price': 280, 'duration': '3h 15m', 'departure': '09:00'},
    'b': {'provider': 'Sample Express', 'price': 320, 'duration': '2h 50m', 'departure': '10:30'},
}

CSS = '''body{font:16px system-ui;background:#f4f7f6;color:#18312b;margin:0}main{max-width:760px;margin:40px auto;padding:24px;background:white;border-radius:16px}label{display:block;margin:16px 0}input{display:block;padding:10px;font:inherit;width:90%;margin-top:5px}button,a{font:inherit}button{padding:10px 16px;background:#176653;color:white;border:0;border-radius:8px;cursor:pointer}button:disabled{background:#64748b}nav{display:flex;gap:16px;flex-wrap:wrap}aside{background:#fff2d5;padding:12px}article{border:1px solid #cbd5d1;padding:16px;margin-top:14px;border-radius:10px}a{color:#145c50}'''


def page(title: str, body: str, script: str = '') -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | Sahaj Demo</title><style>{CSS}</style></head><body><main><nav><a href="/">Home</a><a href="/demo/bus">Bus</a><a href="/demo/bill">Bill</a><a href="/demo/scheme">Scheme</a></nav><h1>{escape(title)}</h1><aside>Fictional demonstration only. No real bookings, eligibility decisions, or payments.</aside>{body}</main><script>{script}</script></body></html>'''


def bus():
    return page('Bus ticket search', '''<p>Search for a sample trip from Bengaluru to Mysuru.</p><label>Origin<input id="from" autocomplete="off"></label><label>Destination<input id="to" autocomplete="off"></label><button id="search-buses" type="button">Search buses</button><section id="result" aria-live="polite" hidden><h2>Available buses</h2><p>Two fictional providers are available for this sample route.</p><article><h3>Demo Transit</h3><p>₹280 • 09:00 • 3h 15m</p><a href="/demo/provider/a">View offer</a></article><article><h3>Sample Express</h3><p>₹320 • 10:30 • 2h 50m</p><a href="/demo/provider/b">View offer</a></article><p>Booking and payment are disabled in the demo.</p><button disabled>Proceed to checkout (disabled)</button></section>''', "document.getElementById('search-buses').onclick=()=>{document.getElementById('result').hidden=false;};")


def bill():
    return page('Electricity bill portal', '''<p>Look up a fictional electricity bill. Use sample ID DEMO-1042 only.</p><label>Consumer ID<input id="consumer-id" autocomplete="off"></label><button id="lookup-bill" type="button">Find bill</button><section id="result" aria-live="polite" hidden><h2>Sample bill</h2><p>Amount due: ₹745</p><p>Status: Unpaid (fictional)</p><p>No real account or payment is connected.</p><button disabled>Pay now (disabled)</button></section>''', "document.getElementById('lookup-bill').onclick=()=>{document.getElementById('result').hidden=false;};")


def scheme():
    return page('Public scheme information', '''<p>Explore a fictional education support scheme. This is not a government website.</p><label>District<input id="district" autocomplete="off"></label><button id="check-scheme" type="button">View sample scheme</button><section id="result" aria-live="polite" hidden><h2>Example education support scheme</h2><p>Sample documents: proof of enrolment and residence.</p><p>Eligibility must be checked on official sources. No application is submitted.</p><button disabled>Submit application (disabled)</button></section>''', "document.getElementById('check-scheme').onclick=()=>{document.getElementById('result').hidden=false;};")


def provider(key):
    o = OFFERS[key]
    return page(o['provider'], f'''<article id="offer" data-provider="{o['provider']}" data-price="{o['price']}" data-duration="{o['duration']}" data-departure="{o['departure']}"><h2>Bengaluru → Mysuru</h2><p>Price: ₹{o['price']}</p><p>Departure: {o['departure']}</p><p>Duration: {o['duration']}</p><button disabled>Book now (disabled)</button></article>''')
