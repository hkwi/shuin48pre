import lxml.html
import re
import csv
import urllib.parse

urls = [("http://www.asahi.com/senkyo/senkyo2017/kaihyo/A%02d.html" % i, False) for i in range(1, 48)]
urls += [("http://www.asahi.com/senkyo/senkyo2017/kaihyo/O%02d.html" % i, True) for i in range(1, 12)]

keys = "area hirei od rose num percent sei mei age party status w career".split()

def run(fp):
	out = csv.writer(fp)
	for url,hirei in urls:
		doc = lxml.html.parse(url)
		area_or_party = None
		for block in doc.xpath('.//*[@id="KaihyoArea"]//*[@class="snkH2Box" or @class="snkTbl01"]'):
			if block.tag == "div":
				area_or_party = block
				continue
			for p in block.xpath('.//tr'):
				r = dict(
					rose = p.xpath('.//td[@class="rose"]//span/@title'),
					sei = p.xpath('.//td[@class="namae"]//*[@class="sei"]/text()'),
					mei = p.xpath('.//td[@class="namae"]//*[@class="mei"]/text()'),
					age = p.xpath('.//td[@class="namae"]//*[@class="age"]/text()'),
					num = p.xpath('.//td[@class="num"]/div/text()'),
					percent = p.xpath('.//td[@class="num"]/div/span/text()'),
					career = p.xpath('.//td[@class="career"]//text()'),
					status = p.xpath('.//td[@class="status"]//text()'),
					tosenkaisu = p.xpath('.//td[@class="tosenkaisu"]/div/text()'),
					w = p.xpath('.//td[@class="w"]//*/text()'),
				)
				if hirei:
					r["od"] = p.xpath('.//td[@class="lstNum"]/div/text()')
					r["hirei"] = doc.xpath('.//div[@class="Title"]/p/text()')
					r["party"] = area_or_party.xpath('.//h2/text()')
				else:
					r["area"] = area_or_party.xpath('.//h2/text()')
					r["party"] = p.xpath('.//td[@class="party"]//text()')
				
				for k,v in r.items():
					r[k] = " ".join([s.strip() for s in v if s.strip()])
				
				m = re.match("^比例区候補者：(.*)ブロック（定数(\d+)）$", r.get("hirei",""))
				if m:
					r["hirei"] = m.group(1)
					r["hirei_num_posts"] = m.group(2)
				
				r["url"] = url
				out.writerow([r.get(k) for k in keys])

if __name__=="__main__":
	import sys
	run(sys.stdout)
