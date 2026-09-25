"""Loopback-only local dashboard server; Python standard library only."""
import argparse
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import engine
ROOT=Path(__file__).resolve().parent
ALLOWED={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/config.json':'config.json','/example.json':'example.json'}
TYPES={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'}

class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,kind='application/json'):
        self.send_response(status)
        self.send_header('Content-Type',kind+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=self.path.split('?')[0]
        if path not in ALLOWED:
            return self.send(404,b'{"error":"Not found"}')
        file=ROOT/ALLOWED[path]
        self.send(200,file.read_bytes(),TYPES[file.suffix])
    def do_POST(self):
        if self.path!='/api/run': return self.send(404,b'{"error":"Not found"}')
        # Do not accept cross-origin requests from arbitrary web pages.
        origin=self.headers.get('Origin')
        if origin and origin != 'http://'+self.headers.get('Host',''):
            return self.send(403,b'{"error":"Cross-origin requests are not accepted"}')
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=1000000: raise ValueError('Input must be 1 byte to 1 MB')
            if 'application/json' not in self.headers.get('Content-Type',''):
                raise ValueError('Send application/json input')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('Input must be a JSON object')
            result=engine.run(data)
            result['dataset_label']=str(data.get('dataset_label','User-supplied data; provenance not verified'))
            self.send(200,json.dumps(result,allow_nan=False).encode())
        except (ValueError,TypeError,KeyError,IndexError,OverflowError,ZeroDivisionError) as exc:
            self.send(400,json.dumps({'error':'Check your input: '+str(exc)}).encode())
    def log_message(self,*args): pass

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000); args=parser.parse_args()
    print(f'Open http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
