"""Serve the article locally with byte ranges for native video chapter seeking."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import re

ROOT=Path(__file__).resolve().parents[1]

class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-store')
        super().end_headers()

    def send_head(self):
        self.range_length=None
        value=self.headers.get('Range')
        path=Path(self.translate_path(self.path))
        if not value or not path.is_file(): return super().send_head()
        size=path.stat().st_size
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',value.strip())
        if not match or not any(match.groups()) or size==0:
            return self.invalid_range(size)
        left,right=match.groups()
        if left:
            start=int(left);end=min(int(right),size-1) if right else size-1
        else:
            count=int(right)
            if not count:return self.invalid_range(size)
            start=max(0,size-count);end=size-1
        if start>=size or end<start:return self.invalid_range(size)
        stream=path.open('rb')
        stream.seek(start)
        self.range_length=end-start+1
        self.send_response(206)
        self.send_header('Content-type',self.guess_type(str(path)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(self.range_length))
        self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
        self.end_headers()
        return stream

    def invalid_range(self,size):
        self.send_response(416)
        self.send_header('Content-Range',f'bytes */{size}')
        self.send_header('Content-Length','0')
        self.end_headers()
        return None

    def copyfile(self,source,outputfile):
        if self.range_length is None:return super().copyfile(source,outputfile)
        remaining=self.range_length
        try:
            while remaining:
                chunk=source.read(min(65536,remaining))
                if not chunk:break
                outputfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):
            pass  # A browser can cancel one range before requesting another.

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(PreviewHandler,directory=str(ROOT)))
    print(f'SEVEN preview: http://127.0.0.1:{args.port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
