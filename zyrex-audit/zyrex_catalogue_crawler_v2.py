#!/usr/bin/env python3
import argparse,csv,hashlib,json,re,time,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse,urlunparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UA='ZyrexCatalogueAudit/2.0 (public catalogue audit)'; MAXWORDS=180

def ws(s): return re.sub(r'\s+',' ',s or '').strip()
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def lim(s,n):
    w=ws(s).split(); return ' '.join(w[:n])+(' …' if len(w)>n else '')
def htmltext(s): return ws(BeautifulSoup(s or '','html.parser').get_text(' ',strip=True))
def canon(u):
    p=urlparse(u); path=re.sub(r'/+','/',p.path)
    if '/product/' in path and not path.endswith('/'): path+='/'
    return urlunparse((p.scheme or 'https',p.netloc.lower(),path,'','',''))
def money_text(s):
    m=re.search(r'([0-9][0-9,]*(?:\.[0-9]+)?)',s or ''); return float(m.group(1).replace(',','')) if m else None
def session():
    s=requests.Session(); retry=Retry(total=4,backoff_factor=.8,status_forcelist=(429,500,502,503,504),respect_retry_after_header=True)
    s.mount('https://',HTTPAdapter(max_retries=retry,pool_connections=10,pool_maxsize=10)); s.headers['User-Agent']=UA; return s
def get(s,u,**kw):
    r=s.get(u,timeout=30,**kw); r.raise_for_status(); return r

def robots(s,base):
    rp=RobotFileParser(); rp.set_url(urljoin(base,'robots.txt'))
    try: rp.parse(get(s,rp.url).text.splitlines())
    except Exception: rp.parse(['User-agent: *','Allow: /'])
    return rp

def section(t,names,n):
    lab='|'.join(re.escape(x) for x in names)
    pat=rf'(?:^|\b)(?:{lab})\s*[:\-]?\s*(.+?)(?=(?:\b(?:ingredients?|composition|benefits?|uses?|usage|directions?|dosage|dose|warning|warnings|precautions?|contraindications?|how to use)\b\s*[:\-]?)|$)'
    m=re.search(pat,t,re.I); return lim(m.group(1),n) if m else ''
def risk(name,cats,text):
    t=' '.join([name,*cats,text[:2000]]).lower()
    if any(x in t for x in ['cancer','kidney failure','liver failure','creatinine','bhasma','parad','tamra','swarna']): return 'HIGH'
    if any(x in t for x in ['asthma','bronchitis','diabetes','blood pressure','tinnitus','vitiligo','hemorrhoid','piles','pregnan','child','children']): return 'MODERATE'
    return 'STANDARD'
def variant(name):
    s=name.lower(); s=re.sub(r'\b(pack\s+of\s+)?\d+(?:\.\d+)?\s*(kg|g|gm|gram|ml|l|tablets?|capsules?|bottles?|pouches?)\b',' ',s)
    s=re.sub(r'\b(tablets?|capsules?|powder|oil|tonic|extract|liquid|ointment|malham|bhasma)\b',' ',s)
    return ws(re.sub(r'[^a-z0-9]+',' ',s))
def pack_form(name):
    pack=''; m=re.search(r'\b(?:pack\s+of\s+)?\d+(?:\.\d+)?\s*(kg|g|gm|gram|ml|l|tablets?|capsules?|bottles?|pouches?)\b',name,re.I)
    if m: pack=m.group(0)
    form=''
    for x in ['liquid extract','tablet','capsule','powder','oil','tonic','ointment','malham','bhasma']:
        if x in name.lower(): form=x.title(); break
    return pack,form
def recommendation(rr):
    if rr=='HIGH': return 'Catalogue matching only; never diagnose, promise cure, replace emergency/medical treatment, or advise stopping prescribed care.'
    if rr=='MODERATE': return 'May compare by stated goal; avoid disease-treatment guarantees and recommend professional advice when symptoms, pregnancy/age, or medicines create material risk.'
    return 'May compare by shopper-stated goal and official product attributes. Do not invent benefits, safety, dosage, or contraindications.'
def build_record(name,url,cats,desc,regular,sale,stock,sku,source_status,source_hash):
    ing=section(desc,['ingredients','ingredient','composition'],55); use=section(desc,['benefits','benefit','uses','use'],35)
    dose=section(desc,['directions','direction','dosage','dose','how to use','usage'],30); warn=section(desc,['warnings','warning','precautions','precaution','contraindications','contraindication'],30)
    rem=max(20,MAXWORDS-sum(len(x.split()) for x in [ing,use,dose,warn])); dex=lim(desc,rem)
    pack,form=pack_form(name); rr=risk(name,cats,desc)
    return {'registry_id':'','exact_product_name':name,'canonical_url':canon(url),'categories':cats,'formulation_type':form,'ingredients_composition_official':ing,'strength_concentration':'','pack_size_quantity':pack,'regular_price_inr':regular,'sale_price_inr':sale,'stock_status':stock,'sku':sku,'official_description_excerpt':dex,'official_stated_uses_benefits':use,'directions_dosage':dose,'warnings_precautions_contraindications':warn,'customer_intent_tags':[],'body_system_wellness_tags':[],'official_purchase_url':canon(url),'zyrex_official_claim':lim(' '.join(x for x in [use,dex] if x),MAXWORDS),'general_information':'Not populated by crawler; source independently later.','recommendation_allowed':recommendation(rr),'source_verification_status':source_status,'possible_variant_group':variant(name),'source_sha256':source_hash,'last_verified_timestamp':now(),'medical_claim_risk':rr,'notes':'Missing fields are intentionally blank; blank does not prove absence on packaging.'}

def api_price(prices,key):
    if not isinstance(prices,dict): return None
    v=prices.get(key)
    if v in (None,''): return None
    try: return float(v)/(10**int(prices.get('currency_minor_unit',2) or 2))
    except Exception: return None

def store_api_records(s,base,delay):
    ep=urljoin(base,'wp-json/wc/store/v1/products'); raw=[]; total_header=None; pages_header=None; page=1
    while page<=200:
        r=s.get(ep,params={'per_page':100,'page':page},timeout=30)
        if r.status_code in (401,403,404): return [],{'status':r.status_code,'pages_fetched':page-1,'total_header':total_header,'total_pages_header':pages_header}
        r.raise_for_status(); data=r.json()
        if not isinstance(data,list) or not data: break
        if total_header is None:
            try: total_header=int(r.headers.get('X-WP-Total','0') or 0)
            except: total_header=0
            try: pages_header=int(r.headers.get('X-WP-TotalPages','0') or 0)
            except: pages_header=0
        raw.extend(data)
        if (pages_header and page>=pages_header) or len(data)<100: break
        page+=1; time.sleep(delay)
    rows=[]; snapshots=[]
    for p in raw:
        if not isinstance(p,dict): continue
        name=ws(p.get('name')); url=p.get('permalink') or ''
        if not name or '/product/' not in urlparse(url).path: continue
        cats=[ws(x.get('name')) for x in (p.get('categories') or []) if isinstance(x,dict) and ws(x.get('name'))]
        desc=ws(htmltext(p.get('short_description'))+' '+htmltext(p.get('description')))
        prices=p.get('prices') or {}; reg=api_price(prices,'regular_price'); sale=api_price(prices,'sale_price')
        stock='In stock' if p.get('is_in_stock') is True else ('Out of stock' if p.get('is_in_stock') is False else '')
        av=p.get('stock_availability') or {}
        if isinstance(av,dict) and ws(av.get('text')): stock=ws(av.get('text'))
        sku=ws(p.get('sku')); source_hash=hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        rows.append(build_record(name,url,cats,desc,reg,sale,stock,sku,'STORE_API_VERIFIED',source_hash))
        snapshots.append({'canonical_url':canon(url),'source_sha256':source_hash,'source':'WooCommerce Store API','verified_at':now()})
    meta={'status':200,'pages_fetched':page,'total_header':total_header,'total_pages_header':pages_header,'records_received':len(raw),'records_normalized':len(rows)}
    return rows,meta,snapshots

def sitemap_urls(s,base):
    q=[]
    try:
        for l in get(s,urljoin(base,'robots.txt')).text.splitlines():
            if l.lower().startswith('sitemap:'): q.append(l.split(':',1)[1].strip())
    except Exception: pass
    q += [urljoin(base,x) for x in ('sitemap_index.xml','sitemap.xml','wp-sitemap.xml')]
    seen=set(); out=set(); host=urlparse(base).netloc
    while q and len(seen)<500:
        u=q.pop(0)
        if u in seen: continue
        seen.add(u)
        try: root=ET.fromstring(get(s,u).text)
        except Exception: continue
        loc=[ws(x.text) for x in root.iter() if x.tag.endswith('loc')]
        if root.tag.endswith('sitemapindex'): q += [x for x in loc if urlparse(x).netloc==host]
        else: out |= {canon(x) for x in loc if urlparse(x).netloc==host and '/product/' in urlparse(x).path}
    return out

def links(html,base):
    soup=BeautifulSoup(html,'html.parser'); host=urlparse(base).netloc; out=set()
    for a in soup.find_all('a',href=True):
        u=urljoin(base,a['href'])
        if urlparse(u).netloc==host and '/product/' in urlparse(u).path: out.add(canon(u))
    return out

def shop_urls(s,base,delay):
    first=get(s,urljoin(base,'shop/')).text; out=links(first,base); soup=BeautifulSoup(first,'html.parser'); pages=1
    for a in soup.select('a.page-numbers,.woocommerce-pagination a'):
        t=ws(a.get_text()); m=re.search(r'/page/(\d+)/',a.get('href',''))
        if t.isdigit(): pages=max(pages,int(t))
        if m: pages=max(pages,int(m.group(1)))
    m=re.search(r'Showing\s+\d+[–-]\d+\s+of\s+([\d,]+)\s+results',ws(soup.get_text(' ',strip=True)),re.I)
    if m: pages=max(pages,(int(m.group(1).replace(',',''))+11)//12)
    for p in range(2,pages+1):
        try: out |= links(get(s,urljoin(base,f'shop/page/{p}/')).text,base)
        except Exception as e: print('WARN shop page',p,e,flush=True)
        if p%25==0: print('shop',p,'/',pages,'urls',len(out),flush=True)
        time.sleep(delay)
    return out,pages

def text1(soup,sel):
    n=soup.select_one(sel); return ws(n.get_text(' ',strip=True)) if n else ''
def parse_html_product(url,rp,delay):
    if not rp.can_fetch(UA,url): raise PermissionError('robots.txt disallows URL')
    s=session(); r=get(s,url); soup=BeautifulSoup(r.text,'html.parser')
    name=text1(soup,'h1.product_title') or text1(soup,'h1.entry-title') or text1(soup,'h1')
    if not name: raise ValueError('missing product name')
    can=soup.find('link',rel=lambda x:x and 'canonical' in x); cu=canon(can.get('href')) if can and can.get('href') else canon(url)
    cats=list(dict.fromkeys(ws(a.get_text(' ',strip=True)) for a in soup.select('.posted_in a') if ws(a.get_text(' ',strip=True))))
    desc=ws(text1(soup,'.woocommerce-product-details__short-description')+' '+(text1(soup,'#tab-description') or text1(soup,'.woocommerce-Tabs-panel--description')))
    box=soup.select_one('p.price,.summary .price'); reg=sale=None
    if box:
        d=box.select_one('del'); i=box.select_one('ins'); reg=money_text(d.get_text()) if d else None; sale=money_text(i.get_text()) if i else money_text(box.get_text())
    stock=text1(soup,'p.stock') or text1(soup,'.stock'); sku=text1(soup,'.sku'); h=hashlib.sha256(r.content).hexdigest(); time.sleep(delay)
    return build_record(name,cu,cats,desc,reg,sale,stock,sku,'PRODUCT_PAGE_VERIFIED',h)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='https://zyrexayurveda.com/'); ap.add_argument('--out-dir',default='data/zyrex'); ap.add_argument('--expected-min',type=int,default=4000); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--delay',type=float,default=.15); a=ap.parse_args()
    base=a.base_url.rstrip('/')+'/'; out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); rep=Path('reports/zyrex'); rep.mkdir(parents=True,exist_ok=True); s=session(); rp=robots(s,base)
    api_rows,api_meta,snapshots=store_api_records(s,base,a.delay); print('store api',api_meta,flush=True)
    by={r['canonical_url']:r for r in api_rows}; urls=set(by); counts={'store_api':api_meta}; shop_pages=0; html_attempted=0; fail=[]
    if len(urls)<a.expected_min:
        sm=sitemap_urls(s,base); urls|=sm; counts['sitemap_product_urls']=len(sm); print('sitemap total union',len(urls),flush=True)
    if len(urls)<a.expected_min:
        sh,shop_pages=shop_urls(s,base,a.delay); urls|=sh; counts['shop_pagination_product_urls']=len(sh); print('shop total union',len(urls),flush=True)
    urls={u for u in urls if rp.can_fetch(UA,u)}; missing=sorted(urls-set(by)); print('official API records',len(by),'html fallback needed',len(missing),flush=True)
    if missing:
        html_attempted=len(missing)
        with ThreadPoolExecutor(max_workers=max(1,a.workers)) as ex:
            fs={ex.submit(parse_html_product,u,rp,a.delay):u for u in missing}
            for i,f in enumerate(as_completed(fs),1):
                try:
                    r=f.result(); by[r['canonical_url']]=r; snapshots.append({'canonical_url':r['canonical_url'],'source_sha256':r['source_sha256'],'source':'Product HTML','verified_at':r['last_verified_timestamp']})
                except Exception as e: fail.append({'url':fs[f],'error':f'{type(e).__name__}: {e}'})
                if i%100==0 or i==len(fs): print('html processed',i,'/',len(fs),'ok',len(by),'fail',len(fail),flush=True)
    ok=sorted(by.values(),key=lambda r:(r['exact_product_name'].lower(),r['canonical_url'])); raw_before=len(api_rows)+(html_attempted-len(fail)); duplicates_resolved=max(0,raw_before-len(ok))
    for i,r in enumerate(ok,1): r['registry_id']=f'ZYX-{i:05d}'
    groups={}
    for r in ok: groups.setdefault(r['possible_variant_group'],[]).append(r['registry_id'])
    groups={k:v for k,v in groups.items() if k and len(v)>1}
    (out/'product_urls.txt').write_text('\n'.join(sorted(urls))+'\n',encoding='utf-8')
    with (out/'products.jsonl').open('w',encoding='utf-8') as f:
        for r in ok: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with (out/'source_snapshots.jsonl').open('w',encoding='utf-8') as f:
        for r in snapshots: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with (out/'failed_urls.jsonl').open('w',encoding='utf-8') as f:
        for r in fail: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    if ok:
        with (out/'products.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(ok[0])); w.writeheader()
            for r in ok: w.writerow({k:(' | '.join(v) if isinstance(v,list) else v) for k,v in r.items()})
    cats=sorted({c for r in ok for c in r['categories'] if c}); hi=sum(r['medical_claim_risk']=='HIGH' for r in ok); mod=sum(r['medical_claim_risk']=='MODERATE' for r in ok)
    req=['canonical_url','categories','formulation_type','pack_size_quantity','stock_status','zyrex_official_claim','recommendation_allowed']
    complete=sum(all(r.get(k) not in ('',None,[]) for k in req) and r.get('regular_price_inr') is not None for r in ok)
    missing_data=sum(any(r.get(k) in ('',None,[]) for k in ['ingredients_composition_official','directions_dosage','warnings_precautions_contraindications']) for r in ok); partial=len(ok)-complete
    man={'project':'ZYREX_FULL_PRODUCT_REGISTRY','base_url':base,'generated_at_utc':now(),'enumeration_sources':counts,'product_urls_discovered':len(urls),'product_pages_fetched':html_attempted,'unique_canonical_products':len(ok),'duplicates_resolved':duplicates_resolved,'failed_product_pages':len(fail),'possible_variant_groups':len(groups),'categories_covered':len(cats),'category_names':cats,'complete_records':complete,'partial_records':partial,'missing_data_records':missing_data,'high_risk_claim_records':hi,'moderate_risk_claim_records':mod,'expected_minimum_gate':a.expected_min,'gate_passed':len(ok)>=a.expected_min,'source_text_policy':f'<= {MAXWORDS} source-derived words retained per product; canonical source URL and SHA-256 retained.'}
    (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2),encoding='utf-8'); (out/'possible_variant_groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf-8')
    report=f"# ZYREX FULL PRODUCT REGISTRY — CRAWL REPORT\n\nGenerated: {man['generated_at_utc']}\n\n- Product URLs discovered: **{len(urls)}**\n- Unique source-verified products: **{len(ok)}**\n- Individual HTML product pages fetched: **{html_attempted}**\n- Failed HTML product pages: **{len(fail)}**\n- Possible variant groups: **{len(groups)}**\n- Duplicates resolved: **{duplicates_resolved}**\n- Categories covered: **{len(cats)}**\n- Strict complete records: **{complete}**\n- Partial records: **{partial}**\n- Records missing one or more ingredients/dosage/warnings fields: **{missing_data}**\n- High-risk claim records: **{hi}**\n- Moderate-risk claim records: **{mod}**\n- Expected-minimum gate ({a.expected_min}): **{'PASS' if man['gate_passed'] else 'FAIL'}**\n\nThe official WooCommerce Store API is preferred when complete; individual product HTML is fetched only as a fallback. Blank fields are never filled by inference. Zyrex claims remain separate from independent information and recommendation permission.\n"
    (rep/'CRAWL_REPORT.md').write_text(report,encoding='utf-8'); print(json.dumps(man,indent=2),flush=True)
    return 0 if man['gate_passed'] else 2
if __name__=='__main__': raise SystemExit(main())
