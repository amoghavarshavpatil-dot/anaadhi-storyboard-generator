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

UA='ZyrexCatalogueAudit/1.0 (public catalogue audit)'; MAXWORDS=180

def ws(s): return re.sub(r'\s+',' ',s or '').strip()
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def lim(s,n):
 w=ws(s).split(); return ' '.join(w[:n])+(' …' if len(w)>n else '')
def canon(u):
 p=urlparse(u); path=re.sub(r'/+','/',p.path)
 if '/product/' in path and not path.endswith('/'): path+='/'
 return urlunparse((p.scheme or 'https',p.netloc.lower(),path,'','',''))
def money(s):
 m=re.search(r'([0-9][0-9,]*(?:\.[0-9]+)?)',s or ''); return float(m.group(1).replace(',','')) if m else None
def sess():
 s=requests.Session(); r=Retry(total=4,backoff_factor=.8,status_forcelist=(429,500,502,503,504),respect_retry_after_header=True)
 s.mount('https://',HTTPAdapter(max_retries=r,pool_connections=6,pool_maxsize=6)); s.headers['User-Agent']=UA; return s
def get(s,u):
 r=s.get(u,timeout=30); r.raise_for_status(); return r

def robots(s,base):
 rp=RobotFileParser(); rp.set_url(urljoin(base,'robots.txt'))
 try: rp.parse(get(s,rp.url).text.splitlines())
 except Exception: rp.parse(['User-agent: *','Allow: /'])
 return rp

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

def api_urls(s,base,delay):
 out=set(); ep=urljoin(base,'wp-json/wc/store/v1/products')
 for page in range(1,201):
  try:
   r=s.get(ep,params={'per_page':100,'page':page},timeout=30)
   if r.status_code in (401,403,404): break
   r.raise_for_status(); data=r.json()
   if not isinstance(data,list) or not data: break
   for x in data:
    u=x.get('permalink') if isinstance(x,dict) else None
    if u and '/product/' in urlparse(u).path: out.add(canon(u))
   pages=int(r.headers.get('X-WP-TotalPages','0') or 0)
   if (pages and page>=pages) or len(data)<100: break
   time.sleep(delay)
  except Exception: break
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
  except Exception as e: print('WARN page',p,e)
  if p%25==0: print('shop',p,'/',pages,'urls',len(out))
  time.sleep(delay)
 return out

def text1(soup,sel):
 n=soup.select_one(sel); return ws(n.get_text(' ',strip=True)) if n else ''
def section(t,names,n):
 lab='|'.join(re.escape(x) for x in names); pat=rf'(?:^|\b)(?:{lab})\s*[:\-]?\s*(.+?)(?=(?:\b(?:ingredients?|composition|benefits?|uses?|usage|directions?|dosage|dose|warning|warnings|precautions?|contraindications?|how to use)\b\s*[:\-]?)|$)'
 m=re.search(pat,t,re.I); return lim(m.group(1),n) if m else ''
def risk(name,cats,text):
 t=' '.join([name,*cats,text[:1500]]).lower()
 if any(x in t for x in ['cancer','kidney failure','liver failure','creatinine','bhasma','parad bhasma','tamra bhasma','swarna bhasma']): return 'HIGH'
 if any(x in t for x in ['asthma','bronchitis','diabetes','blood pressure','tinnitus','vitiligo','hemorrhoid','piles']): return 'MODERATE'
 return 'STANDARD'
def variant(name):
 s=name.lower(); s=re.sub(r'\b(pack\s+of\s+)?\d+(?:\.\d+)?\s*(kg|g|gm|gram|ml|l|tablets?|capsules?|bottles?|pouches?)\b',' ',s); s=re.sub(r'\b(tablets?|capsules?|powder|oil|tonic|extract|liquid|ointment|malham)\b',' ',s); return ws(re.sub(r'[^a-z0-9]+',' ',s))

def parse_product(url,rp,delay):
 if not rp.can_fetch(UA,url): raise PermissionError('robots.txt disallows URL')
 s=sess(); r=get(s,url); soup=BeautifulSoup(r.text,'html.parser')
 name=text1(soup,'h1.product_title') or text1(soup,'h1.entry-title') or text1(soup,'h1')
 if not name: raise ValueError('missing product name')
 can=soup.find('link',rel=lambda x:x and 'canonical' in x); cu=canon(can.get('href')) if can and can.get('href') else canon(url)
 cats=list(dict.fromkeys(ws(a.get_text(' ',strip=True)) for a in soup.select('.posted_in a,.product_meta a[rel="tag"]') if ws(a.get_text(' ',strip=True))))
 short=text1(soup,'.woocommerce-product-details__short-description'); long=text1(soup,'#tab-description') or text1(soup,'.woocommerce-Tabs-panel--description'); desc=ws(short+' '+long)
 ing=section(desc,['ingredients','ingredient','composition'],55); use=section(desc,['benefits','benefit','uses','use'],35); dose=section(desc,['directions','direction','dosage','dose','how to use','usage'],30); warn=section(desc,['warnings','warning','precautions','precaution','contraindications','contraindication'],30)
 rem=max(20,MAXWORDS-sum(len(x.split()) for x in [ing,use,dose,warn])); dex=lim(desc,rem)
 box=soup.select_one('p.price,.summary .price'); reg=sale=None
 if box:
  d=box.select_one('del'); i=box.select_one('ins'); reg=money(d.get_text()) if d else None; sale=money(i.get_text()) if i else money(box.get_text())
 stock=text1(soup,'p.stock') or text1(soup,'.stock'); sku=text1(soup,'.sku')
 pack=''; m=re.search(r'\b(?:pack\s+of\s+)?\d+(?:\.\d+)?\s*(kg|g|gm|gram|ml|l|tablets?|capsules?|bottles?|pouches?)\b',name,re.I)
 if m: pack=m.group(0)
 form=''
 for x in ['liquid extract','tablet','capsule','powder','oil','tonic','ointment','malham','bhasma']:
  if x in name.lower(): form=x.title(); break
 rr=risk(name,cats,soup.get_text(' ',strip=True)); rec='May compare by shopper-stated goal and official product attributes. Do not invent benefits, safety, dosage, or contraindications.'
 if rr=='HIGH': rec='Catalogue matching only; never diagnose, promise cure, replace emergency/medical treatment, or advise stopping prescribed care.'
 elif rr=='MODERATE': rec='May compare by stated goal; avoid disease-treatment guarantees and recommend professional advice when symptoms or medicines create material risk.'
 time.sleep(delay)
 return {'registry_id':'','exact_product_name':name,'canonical_url':cu,'categories':cats,'formulation_type':form,'ingredients_composition_official':ing,'strength_concentration':'','pack_size_quantity':pack,'regular_price_inr':reg,'sale_price_inr':sale,'stock_status':stock,'sku':sku,'official_description_excerpt':dex,'official_stated_uses_benefits':use,'directions_dosage':dose,'warnings_precautions_contraindications':warn,'customer_intent_tags':[],'body_system_wellness_tags':[],'official_purchase_url':cu,'zyrex_official_claim':lim(' '.join(x for x in [use,dex] if x),MAXWORDS),'general_information':'Not populated by crawler; source independently later.','recommendation_allowed':rec,'source_verification_status':'PRODUCT_PAGE_VERIFIED','possible_variant_group':variant(name),'source_sha256':hashlib.sha256(r.content).hexdigest(),'last_verified_timestamp':now(),'medical_claim_risk':rr,'notes':'Missing fields are intentionally blank; blank does not prove absence on packaging.'}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--base-url',default='https://zyrexayurveda.com/'); ap.add_argument('--out-dir',default='data/zyrex'); ap.add_argument('--expected-min',type=int,default=4000); ap.add_argument('--workers',type=int,default=2); ap.add_argument('--delay',type=float,default=.2); a=ap.parse_args()
 base=a.base_url.rstrip('/')+'/'; out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); rep=Path('reports/zyrex'); rep.mkdir(parents=True,exist_ok=True); s=sess(); rp=robots(s,base)
 urls=sitemap_urls(s,base); counts={'sitemap':len(urls)}; print('sitemap',len(urls))
 if len(urls)<a.expected_min: x=api_urls(s,base,a.delay); counts['store_api']=len(x); urls|=x; print('api total',len(urls))
 if len(urls)<a.expected_min: x=shop_urls(s,base,a.delay); counts['shop_pagination']=len(x); urls|=x; print('shop total',len(urls))
 urls=sorted(u for u in urls if rp.can_fetch(UA,u)); (out/'product_urls.txt').write_text('\n'.join(urls)+'\n',encoding='utf-8')
 ok=[]; fail=[]
 with ThreadPoolExecutor(max_workers=max(1,a.workers)) as ex:
  fs={ex.submit(parse_product,u,rp,a.delay):u for u in urls}
  for i,f in enumerate(as_completed(fs),1):
   try: ok.append(f.result())
   except Exception as e: fail.append({'url':fs[f],'error':f'{type(e).__name__}: {e}'})
   if i%100==0 or i==len(fs): print('processed',i,'/',len(fs),'ok',len(ok),'fail',len(fail))
 by={}
 for r in ok: by.setdefault(r['canonical_url'],r)
 ok=sorted(by.values(),key=lambda r:(r['exact_product_name'].lower(),r['canonical_url']))
 for i,r in enumerate(ok,1): r['registry_id']=f'ZYX-{i:05d}'
 groups={}
 for r in ok: groups.setdefault(r['possible_variant_group'],[]).append(r['registry_id'])
 groups={k:v for k,v in groups.items() if k and len(v)>1}
 with (out/'products.jsonl').open('w',encoding='utf-8') as f:
  for r in ok: f.write(json.dumps(r,ensure_ascii=False)+'\n')
 with (out/'failed_urls.jsonl').open('w',encoding='utf-8') as f:
  for r in fail: f.write(json.dumps(r,ensure_ascii=False)+'\n')
 if ok:
  with (out/'products.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(ok[0])); w.writeheader()
   for r in ok:
    z={k:(' | '.join(v) if isinstance(v,list) else v) for k,v in r.items()}; w.writerow(z)
 man={'project':'ZYREX_FULL_PRODUCT_REGISTRY','base_url':base,'generated_at_utc':now(),'enumeration_sources':counts,'product_urls_discovered':len(urls),'unique_canonical_products':len(ok),'failed_product_pages':len(fail),'possible_variant_groups':len(groups),'expected_minimum_gate':a.expected_min,'gate_passed':len(urls)>=a.expected_min,'source_text_policy':f'<= {MAXWORDS} source-derived words retained per product; canonical URL and SHA-256 retained for audit.'}
 (out/'manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2),encoding='utf-8'); (out/'possible_variant_groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding='utf-8')
 missing=sum(1 for r in ok if not r['ingredients_composition_official'] or not r['directions_dosage'] or not r['warnings_precautions_contraindications']); hi=sum(r['medical_claim_risk']=='HIGH' for r in ok); mod=sum(r['medical_claim_risk']=='MODERATE' for r in ok)
 report=f"# ZYREX FULL PRODUCT REGISTRY — CRAWL REPORT\n\nGenerated: {man['generated_at_utc']}\n\n- Product URLs discovered: **{len(urls)}**\n- Canonical product pages verified: **{len(ok)}**\n- Failed product pages: **{len(fail)}**\n- Possible variant groups: **{len(groups)}**\n- Records missing ingredients/dosage/warnings on public page: **{missing}**\n- High-risk claim records: **{hi}**\n- Moderate-risk claim records: **{mod}**\n- Expected-minimum gate ({a.expected_min}): **{'PASS' if man['gate_passed'] else 'FAIL'}**\n\nBlank fields are never filled by inference. Zyrex claims remain separate from independent information and recommendation permission.\n"
 (rep/'CRAWL_REPORT.md').write_text(report,encoding='utf-8')
 return 0 if man['gate_passed'] and ok else 2
if __name__=='__main__': raise SystemExit(main())
