import csv
import lxml.html
import urllib.request

def run(fp):
	fieldnames = "name area twitter facebook youtube line bio".split()
	
	out = csv.writer(fp)
	d = lxml.html.parse(urllib.request.urlopen("https://www.komei.or.jp/campaign/shuin2017/"))
	ps = d.xpath('.//div[contains(@class, "division")]')
	for p in ps:
		bulk = dict(
			na = p.xpath('./h1/img/@alt'),
			bio = p.xpath('./p/text()'),
			youtube = p.xpath('.//img[@src="img/ic-youtube.png"]/parent::a/@href'),
			facebook = p.xpath('.//img[@src="img/ic-facebook.png"]/parent::a/@href'),
			twitter = p.xpath('.//img[@src="img/ic-twitter.png"]/parent::a/@href'),
			line = p.xpath('.//img[@src="img/ic-line.png"]/parent::a/@href'),
		)
		for k,v in bulk.items():
			assert len(v)<2
			bulk[k] = "".join(v)
		
		na = bulk["na"].split()
		bulk["name"] = na[0]
		bulk["area"] = na[1]
		
		out.writerow([bulk.get(k) for k in fieldnames])

if __name__=="__main__":
	import sys
	run(sys.stdout)
