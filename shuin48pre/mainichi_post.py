import lxml.html
import urllib.request
import re
import csv
import unicodedata

urls = [("https://mainichi.jp/senkyo/48shu/area/?kid=%02d" % i, False) for i in range(1, 48)]
urls += [("https://mainichi.jp/senkyo/48shu/hirei/?bid=%02d" % i, True) for i in range(1,12)]

keys = "area hirei num mark votes name sei mei age party state url".split()

party_map = {
	"希望の党": "希望",
	"公明党": "公明",
	"幸福実現党": "幸福",
	"自由民主党": "自民",
	"社会民主党": "社民",
	"新党大地": "大地",
	"日本のこころ": "こころ",
	"日本維新の会": "維新",
	"日本共産党": "共産",
	"無": "無所属",
	"立憲": "立憲民主",
	"立憲民主党": "立憲民主",
}

def run(fp):
	out = csv.writer(fp)
	for url,hirei in urls:
		doc = lxml.html.parse(urllib.request.urlopen(url))
		title = None
		for area in doc.xpath('.//div[@id="main"]//h1'):
			if title is None:
				title = area.xpath('.//text()')
				continue
			
			for ul in area.xpath('..//parent::*/following-sibling::ul[1]'):
				for li in ul.xpath('./li'):
					r = dict(
						mark = li.xpath('.//*[@class="ElectedMark"]//text()'),
						name = li.xpath('.//*[@class="namae"]//text()'),
						age = li.xpath('.//*[@class="Age"]//text()'),
						state = li.xpath('.//*[@class="State"]//text()'),
						votes = li.xpath('.//*[@class="VotesCount"]/text()'),
					)
					if hirei:
						r["party"] = area.xpath('./text()')
						r["hirei"] = title
						r["num"] = li.xpath('.//*[@class="Rank"]//text()')
					else:
						r["party"] = li.xpath('.//*[@class="Party"]//text()')
						r["area"] = area.xpath('./text()')
					
					for k,vs in r.items():
						v = " ".join([v.strip() for v in vs if v.strip()])
						r[k] = unicodedata.normalize("NFKC", v)
					
					m = re.match("\((\d+)\)", r.get("age",""))
					if m:
						r["age"] = m.group(1)
					
					seimei = re.split("[　 ]+", r.get("name",""))
					if len(seimei)==2:
						r["sei"] = seimei[0]
						r["mei"] = seimei[1]
					
					r["party"] = party_map.get(r["party"], r["party"])
					
					m = re.match("^比例 (.*)ブロック 定数 \d+$", r.get("hirei",""))
					if m:
						r["hirei"] = m.group(1)
					
					r["url"] = url
					out.writerow([r.get(k) for k in keys])

if __name__=="__main__":
	import sys
	run(sys.stdout)
