import re
import csv
import lxml.html
import urllib.request

def run(fp):
	fieldnames = "name area twitter facebook youtube line bio".split()
	
	out = csv.writer(fp)
	d = lxml.html.parse(urllib.request.urlopen("https://www.komei.or.jp/campaign/shuin2017/hireiku/"))
	hs = d.xpath('.//h2')
	for h in hs:
		if not h.text_content():
			continue
		for n in h.xpath('./following-sibling::node()'):
			if not isinstance(n, lxml.html.HtmlElement):
				continue
			if n.xpath(".//h2"):
				break
			for p in n.xpath('.//div[contains(@class,"hireiku-candidate")]'):
				bulk = dict(
					na = p.xpath('.//h4/img/@alt'),
					bio = p.xpath('./p/text()'),
					youtube = p.xpath('.//img[contains(@src,"ic-youtube.png")]/parent::a/@href'),
					facebook = p.xpath('.//img[contains(@src,"ic-facebook.png")]/parent::a/@href'),
					twitter = p.xpath('.//img[contains(@src,"img/ic-twitter.png")]/parent::a/@href'),
					line = p.xpath('.//img[contains(@src,"img/ic-line.png")]/parent::a/@href'),
				)
				if not len(bulk["na"]):
					break
				for k,v in bulk.items():
					assert len(v)<2
					bulk[k] = "".join(v)
				
				na = re.split("[　 ]", bulk["na"])
				bulk["name"] = na[0]
				bulk["prev"] = na[1]
				
				bulk["area"] = h.text_content().split("（")[0].strip()
		
				out.writerow([bulk.get(k) for k in fieldnames])

if __name__=="__main__":
	import sys
	run(sys.stdout)
