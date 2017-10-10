import lxml.html
import re
import csv

urls = [("http://www.asahi.com/senkyo/senkyo2017/koho/A%02d.html" % i, False) for i in range(1, 48)]
urls += [("http://www.asahi.com/senkyo/senkyo2017/koho/O%02d.html" % i, True) for i in range(1, 12)]

keys = "area hirei num hirei_num_posts sei mei sei_hira mei_hira age party support status tousenkaisu w career".split()

def run(fp):
	out = csv.writer(fp)
	for url,hirei in urls:
		doc = lxml.html.parse(url)
		for area_or_party in doc.xpath('.//div[@class="areabox"]'):
			for p in area_or_party.xpath('.//tbody'):
				r = dict(
					sei = p.xpath('.//td[@class="Name"]//dt/*[@class="sei"]/text()'),
					mei = p.xpath('.//td[@class="Name"]//dt/*[@class="mei"]/text()'),
					sei_hira = p.xpath('.//td[@class="Name"]//dd/*[@class="sei"]/text()'),
					mei_hira = p.xpath('.//td[@class="Name"]//dd/*[@class="mei"]/text()'),
					age = p.xpath('.//td[@class="Age"]/div/text()'),
					support = p.xpath('.//td[@class="Suisenshiji"]/div/text()'),
					status = p.xpath('.//td[@class="Status"]/div/text()'),
					tousenkaisu = p.xpath('.//td[@class="Tosenkaisu"]/div/text()'),
					w = p.xpath('.//td[@class="W"]/div/a/text()'),
					career = p.xpath('.//td[@class="Career"]//p/text()'),
				)
				if hirei:
					r["num"] = p.xpath('.//td[@class="lstNum"]/div/text()')
					r["hirei"] = doc.xpath('.//div[@class="Title"]/p/text()')
					r["party"] = area_or_party.xpath('.//h2/text()')
				else:
					r["area"] = area_or_party.xpath('.//h2/text()')
					r["party"] = p.xpath('.//td[@class="Party"]/div/text()')
				
				for k,v in r.items():
					r[k] = " ".join([s.strip() for s in v if s.strip()])
				
				m = re.match("^比例区候補者：(.*)ブロック（定数(\d+)）$", r.get("hirei",""))
				if m:
					r["hirei"] = m.group(1)
					r["hirei_num_posts"] = m.group(2)
				
				out.writerow([r.get(k) for k in keys])

if __name__=="__main__":
	import sys
	run(sys.stdout)
