from email import policy
from email.parser import BytesParser
class MhtmlError(ValueError): pass
def extract_html(data:bytes)->str:
    if not data: raise MhtmlError('The uploaded file is empty.')
    msg=BytesParser(policy=policy.default).parsebytes(data)
    parts=[p for p in msg.walk() if p.get_content_type().lower()=='text/html']
    if not parts:
        text=data.decode('utf-8',errors='replace')
        if '<html' in text.lower() or '<body' in text.lower(): return text
        raise MhtmlError('No HTML MIME part was found.')
    part=max(parts,key=lambda p:p.get_content_disposition()!='attachment')
    try: value=part.get_content()
    except Exception: value=None
    if isinstance(value,str): return value
    raw=part.get_payload(decode=True) or b''
    for enc in (part.get_content_charset(),'utf-8','windows-1252','latin-1'):
        if enc:
            try:return raw.decode(enc)
            except (UnicodeDecodeError,LookupError):pass
    return raw.decode('utf-8',errors='replace')
