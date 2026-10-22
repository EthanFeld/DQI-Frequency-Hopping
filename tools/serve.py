"""Serve the current Qollab JS project locally with an optional Qiskit backend."""
import argparse
import http.server
import json
from pathlib import Path
import sys
import threading

sys.dont_write_bytecode=True
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))


def make_server(project=PROJECT,backend=None,port=8778):
    project=Path(project)
    body=(project/'index.html').read_text(encoding='utf-8')
    page=('<!doctype html><html><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width, initial-scale=1">'
          '<title>DQI · Clearer Hops</title><link rel="stylesheet" href="main.css">'
          '<script type="importmap">{"imports":{"dqi.checkcode_ui":"/__dqi.js"}}</script>'
          '<script>window.backend={__dqi_backend:true};</script></head><body>'+body+
          '<script type="module" src="main.js"></script></body></html>')
    stub='''const fn=name=>({callPromising:async(_backend,...args)=>{
      const response=await fetch('/__call',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name,args})});const result=await response.json();
      if(result.error)throw new Error(result.error);return result.value;}});
      export const backend_info=fn('backend_info');export const live_job=fn('live_job');'''
    lock=threading.Lock()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(project),**kwargs)
        def log_message(self,*args):pass
        def send_body(self,body,kind='application/json',status=200):
            payload=body.encode('utf-8')
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if backend is not None and path in ('/','/index.html'):
                return self.send_body(page,'text/html')
            if backend is not None and path=='/__dqi.js':return self.send_body(stub,'text/javascript')
            if path=='/':self.path='/preview.html'
            return super().do_GET()
        def do_POST(self):
            if backend is None or self.path!='/__call':return self.send_error(404)
            try:
                request=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                from dqi import checkcode_ui
                functions={'backend_info':checkcode_ui.backend_info,'live_job':checkcode_ui.live_job}
                function=functions[request['name']]
                with lock:result=function(backend,*request.get('args',[]))
                self.send_body(json.dumps({'value':result}))
            except Exception as error:
                self.send_body(json.dumps({'error':f'{type(error).__name__}: {error}'}),status=400)

    return http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=('saved','builtin','aer'),default='aer')
    parser.add_argument('--port',type=int,default=8778)
    args=parser.parse_args();backend=None
    if args.backend=='builtin':
        from qiskit.providers.basic_provider import BasicSimulator
        backend=BasicSimulator()
    elif args.backend=='aer':
        from qiskit_aer import AerSimulator
        backend=AerSimulator(method='matrix_product_state',matrix_product_state_truncation_threshold=0,
                             max_parallel_threads=2)
    server=make_server(PROJECT,backend,args.port)
    print(f'DQI {args.backend}: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
