#!/usr/bin/env python3
"""Phase 0: extract KriptoVadász posts (saved Patreon HTML + weekly PDFs) into a normalized corpus.
Usage: ingest_examples.py html START COUNT | pdf | merge"""
import glob, json, os, re, sys, html as htmlmod, subprocess
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EX   = os.path.join(ROOT, 'examples')
OUT  = os.path.join(ROOT, 'crypto-analyst', 'corpus')

class ContentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0; self.started=False; self.done=False
        self.parts=[]; self.imgs=0; self.links=[]
    def handle_starttag(self, tag, attrs):
        if self.done: return
        a=dict(attrs)
        if not self.started:
            if tag=='div' and 'patreon-post-content' in (a.get('class') or ''):
                self.started=True; self.depth=1
            return
        if tag=='div': self.depth+=1
        if tag=='img': self.imgs+=1
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag in ('h1','h2','h3','h4'): self.parts.append('\n\n## ')
        elif tag=='li': self.parts.append('\n- ')
        elif tag in ('p','blockquote','tr'): self.parts.append('\n\n')
        elif tag=='br': self.parts.append('\n')
    def handle_endtag(self, tag):
        if self.done or not self.started: return
        if tag=='div':
            self.depth-=1
            if self.depth<=0: self.done=True
    def handle_data(self, data):
        if self.started and not self.done and data.strip():
            self.parts.append(data)

def extract_html(path):
    h=open(path,encoding='utf-8',errors='ignore').read()
    rec={'file':os.path.basename(path),'kind':'html'}
    m=re.search(r'"datePublished":"([^"]+)"',h); rec['date']=m.group(1)[:10] if m else None
    m=re.search(r'patreon\.com/kriptovadasz/posts/([a-zA-Z0-9\-]+)',h); rec['slug']=m.group(1) if m else None
    m=re.search(r'<title[^>]*>(.*?)</title>',h,re.S)
    t=htmlmod.unescape(m.group(1)).strip() if m else ''
    rec['title']=re.sub(r'\s*[|｜]\s*Kripto.*$','',t).strip()
    i=h.find('patreon-post-content')
    if i==-1:
        rec.update(body='',chars=0,note='no content div'); return rec
    start=h.rfind('<div',0,i)
    p=ContentParser()
    try: p.feed(h[start:start+700000])
    except Exception as e: rec['note']='parse:%s'%e
    body=''.join(p.parts)
    body=re.sub(r'[ \t]+',' ',body)
    body=re.sub(r'\n{3,}','\n\n',body).strip()
    rec['body']=body; rec['images']=p.imgs; rec['chars']=len(body)
    rec['links']=[l for l in p.links if l.startswith('http')][:25]
    return rec

def extract_pdf(path):
    rec={'file':os.path.basename(path),'kind':'pdf'}
    try:
        info=subprocess.run(['pdfinfo',path],capture_output=True,text=True,timeout=20).stdout
        m=re.search(r'Pages:\s+(\d+)',info); rec['pages']=int(m.group(1)) if m else None
    except Exception: pass
    txt=subprocess.run(['pdftotext',path,'-'],capture_output=True,text=True,timeout=40).stdout
    m=re.search(r'(20\d\d)[.\-/ ]+(\d{1,2})[.\-/ ]+(\d{1,2})',txt[:3000])
    rec['date']='%s-%02d-%02d'%(m.group(1),int(m.group(2)),int(m.group(3))) if m else None
    rec['title']='Heti blokklánc elemzés '+(rec['date'] or rec['file'])
    txt=re.sub(r'\n{3,}','\n\n',txt)
    rec['body']=txt.strip(); rec['chars']=len(rec['body'])
    return rec

def main():
    os.makedirs(os.path.join(OUT,'shards'),exist_ok=True)
    mode=sys.argv[1]
    if mode=='html':
        s,c=int(sys.argv[2]),int(sys.argv[3])
        fs=sorted(glob.glob(os.path.join(EX,'*.html')))[s:s+c]
        out=os.path.join(OUT,'shards','html_%03d.jsonl'%s)
        with open(out,'w',encoding='utf-8') as fo:
            for f in fs:
                try: r=extract_html(f)
                except Exception as e: r={'file':os.path.basename(f),'kind':'html','note':'FAIL:%s'%e,'chars':0}
                fo.write(json.dumps(r,ensure_ascii=False)+'\n')
        print('wrote',out,len(fs),'posts')
    elif mode=='pdf':
        fs=sorted(glob.glob(os.path.join(EX,'*.pdf')))
        out=os.path.join(OUT,'shards','pdf_000.jsonl')
        with open(out,'w',encoding='utf-8') as fo:
            for f in fs:
                try: r=extract_pdf(f)
                except Exception as e: r={'file':os.path.basename(f),'kind':'pdf','note':'FAIL:%s'%e,'chars':0}
                fo.write(json.dumps(r,ensure_ascii=False)+'\n')
                print(r['file'][:50], r.get('date'), r.get('pages'), r['chars'])
    elif mode=='merge':
        recs=[]
        for sh in sorted(glob.glob(os.path.join(OUT,'shards','*.jsonl'))):
            recs+= [json.loads(l) for l in open(sh,encoding='utf-8')]
        recs.sort(key=lambda r:(r.get('date') or '0000'))
        with open(os.path.join(OUT,'corpus.jsonl'),'w',encoding='utf-8') as fo:
            for r in recs: fo.write(json.dumps(r,ensure_ascii=False)+'\n')
        dates=[r['date'] for r in recs if r.get('date')]
        empty=[r['file'] for r in recs if r.get('chars',0)<200]
        print('total:',len(recs),'| html:',sum(1 for r in recs if r['kind']=='html'),'| pdf:',sum(1 for r in recs if r['kind']=='pdf'))
        print('date range:',min(dates),'->',max(dates))
        print('total chars:',sum(r.get('chars',0) for r in recs))
        print('thin/empty (<200 chars):',len(empty))
        for f in empty[:15]: print('   -',f[:80])
main()
