import re
import sys
import csv
import lxml.html
import unicodedata

urls = ["http://www.jcp.or.jp/web_senkyo/cat1/"
	] + ["http://www.jcp.or.jp/web_senkyo/cat1/index_%d.html" % s for s in range(2,10)
	] + ["http://www.jcp.or.jp/web_senkyo/cat/"
	] + ["http://www.jcp.or.jp/web_senkyo/cat/index_2.html"]

out = csv.DictWriter(sys.stdout, fieldnames="koho_namel koho_kana age flag block small koho_kata twitter facebook site syubetsu".split())

for url in urls:
	doc = lxml.html.parse(url)
	for e in doc.xpath('.//div[@class="syukoho_wrp" or @class="hireikoho_wrp"]'):
		row = {}
		for cls in "syubetsu senkyo_ku".split():
			i = [txt.strip() for txt in e.xpath('.//span[@class="%s"]/text()' % cls) if txt.strip()]
			if i:
				assert len(i) == 1, i
				row[cls] = unicodedata.normalize("NFKC", i[0])
		senkyo_ku = e.xpath('.//span[@class="senkyo_ku"]/text()').pop()
		for cls in "koho_namel koho_kana koho_agen koho_kata".split():
			i = [txt.strip() for txt in e.xpath('.//div[@class="%s"]/text()' % cls) if txt.strip()]
			if i:
				assert len(i) == 1, i
				row[cls] = unicodedata.normalize("NFKC", i[0])
		for href in e.xpath('.//a/@href'):
			if href.startswith("https://twitter.com/"):
				row["twitter"] = href[len("https://twitter.com/"):]
			elif "facebook.com" in href:
				row["facebook"] = href
			else:
				row["site"] = href
		
		if "重複" in row.get("syubetsu", ""):
			ab = row["senkyo_ku"].split("、")
			if len(ab) == 1 and row["senkyo_ku"].startswith("北海道"):
				a = "北海道"
				b = ab[0]
			else:
				a,b = ab
			row["block"] = a
			row["small"] = b
		elif "小選挙区" == row.get("syubetsu"):
			row["small"] = row["senkyo_ku"]
		elif "比例代表" == row.get("syubetsu"):
			row["block"] = row["senkyo_ku"]
		else:
			assert False, row
		del(row["senkyo_ku"])
		
		pt = row.get("koho_agen")
		if pt:
			pt = unicodedata.normalize("NFKC", pt)
			m = re.match("\(\s*(\d+)\s*\)(.*)", pt.strip())
			assert m, pt
			del(row["koho_agen"])
			row["age"] = m.group(1)
			row["flag"] = m.group(2)
		
		out.writerow(row)
