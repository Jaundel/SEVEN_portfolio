"""Check exact response bytes used by native browser video seeking."""
from pathlib import Path
import urllib.request
import urllib.error

root=Path(__file__).resolve().parents[1]
source=(root/'assets/demo/seven-full-window.mp4').read_bytes()
url='http://127.0.0.1:8765/assets/demo/seven-full-window.mp4'
for request,expected,start,end in [
 ('bytes=0-1023',source[:1024],0,1023),
 ('bytes=123456-',source[123456:],123456,len(source)-1),
 ('bytes=-200',source[-200:],len(source)-200,len(source)-1)]:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':request})) as r:
        assert r.status==206 and r.headers['Accept-Ranges']=='bytes'
        assert r.headers['Content-Range']==f'bytes {start}-{end}/{len(source)}'
        assert int(r.headers['Content-Length'])==len(expected)
        assert r.read()==expected
try:
    urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={len(source)}-'}))
    raise AssertionError('Invalid range accepted')
except urllib.error.HTTPError as e:
    assert e.code==416 and e.headers['Content-Range']==f'bytes */{len(source)}'
print('PASS: exact prefix, offset, suffix and unsatisfiable video ranges')
