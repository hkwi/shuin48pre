import re
import sys
import lxml.etree
import lxml.html
import csv
import urllib.request
import requests

def run(fp):
	fieldnames = "namel name sei mei party cls age_n tw fb site bio age".split()
	out = csv.writer(fp)
	
	d = lxml.etree.parse("http://shugiin.go2senkyo.com/sitemap.xml")
	urls = d.xpath(".//s:loc/text()", namespaces={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"})
	
	h1 = set()
	for url in urls:
		pc = urllib.parse.urlparse(url)
		pcc = pc.path.split("/")
		if pcc[0] == "hirei":
			h1.add(pcc[1])
	for h in h1:
		for i in range(1,20):
			urls.append("http://shugiin.go2senkyo.com/hirei/%s/%d/" % (h,i))
	
	for url in sorted(set(urls)):
		pc = urllib.parse.urlparse(url)
		if pc.netloc != "shugiin.go2senkyo.com":
			continue
		if pc.path == "/":
			continue
		if requests.head(url).status_code != 200:
			continue
		
		doc = lxml.html.parse(url)
		
		areas = doc.xpath('.//span[@class="ttl_txt"]/text()')
		assert len(areas)==1, url
		area = areas.pop().strip()
		
		for p in doc.xpath('.//div[@class="list_peason"]'):
			bulk = dict(
				namel = p.xpath('.//p[@class="list_peason_name"]/text()'),
				cls = p.xpath('.//p[@class="list_peason_txts_d_class"]/text()'),
				age = p.xpath('.//p[@class="list_peason_txts_d_age"]/text()'),
				bio = p.xpath('.//dl[@class="list_person_detail_upper"]/dd/p/text()'),
				site = p.xpath('.//p[@class="list_person_detail_sites_site"]/a/@href'),
				fb = p.xpath('.//p[@class="list_person_detail_sites_facebook"]/a/@href'),
				tw = p.xpath('.//p[@class="list_person_detail_sites_twitter"]/a/@href'),
			)
			if pc.path.startswith("/hirei/"):
				bulk["party"] = doc.xpath('.//p[@class="hirei_sttl_party"]/text()')
			else:
				bulk["party"] = p.xpath('.//span[@class="pname"]/text()')
			
			for k,v in bulk.items():
				bulk[k] = [n.strip() for n in v if n.strip()]
			for k,v in bulk.items():
				assert len(v) < 2, v
				if v:
					bulk[k] = v[0]
				else:
					bulk[k] = None
			
			m = re.match("(\d+)歳", bulk["age"])
			if m:
				bulk["age_n"] = m.group(1)
			
			seimei = re.split("　+", bulk["namel"])
			if len(seimei) > 1:
				bulk["sei"] = seimei[0]
				bulk["mei"] = seimei[1]
				bulk["name"] = "".join(seimei)
			else:
				bulk["name"] = seimei
			out.writerow([bulk.get(k) for k in fieldnames])

if __name__=="__main__":
	run(sys.stdout)
