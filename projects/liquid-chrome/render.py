import sys, time, os, http.server, threading, functools
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__))
args = dict(a.split('=') for a in sys.argv[1:])
scale = args.get('scale', '1'); steps = args.get('steps', '128')
times = [float(x) for x in args['times'].split(',')] if 'times' in args else None
frames = range(int(args.get('start', 0)), int(args.get('end', 360)))
outdir = args.get('out', os.path.join(here, 'frames'))
os.makedirs(outdir, exist_ok=True)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=here, ))
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()
W = round(1080 * float(scale))
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'])
    pg = b.new_page(viewport={'width': W, 'height': W})
    pg.on('console', lambda m: print('console:', m.text))
    pg.on('pageerror', lambda e: print('PAGEERROR', e))
    pg.goto(f'http://127.0.0.1:{srv.server_port}/liquid_chrome.html?t=0&scale={scale}&steps={steps}', timeout=120000)
    pg.wait_for_function('window.__ready === true', timeout=300000)
    items = [(f't{t:.2f}', t) for t in times] if times else [(f'{f:04d}', f / 60) for f in frames]
    for name, t in items:
        path = os.path.join(outdir, f'{name}.png')
        if os.path.exists(path) and not times: continue
        t0 = time.time(); pg.evaluate(f'window.renderAt({t!r})')
        pg.locator('canvas').screenshot(path=path)
        print(name, f'{time.time()-t0:.2f}s', flush=True)
    b.close()
