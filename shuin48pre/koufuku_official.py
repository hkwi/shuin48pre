import re
import csv
import lxml.html
import urllib.request

def run(fp):
	fieldnames = "name namel name_hira area hirei fb tw bl bio url".split()
	
	out = csv.writer(fp)
	d = lxml.html.parse(urllib.request.urlopen("https://candidates.hr-party.jp/elections/2017/1185/"))
	ps = d.xpath('.//div[contains(@class,"p-y-1")]')
	for p in ps:
		r = dict(
			namel = p.xpath(".//rb/text()"),
			name_hira = p.xpath(".//rt/text()"),
			area = p.xpath('.//p[@class="lead"]/text()'),
			bio = p.xpath('.//p[@class="lead"]/following-sibling::p/text()'),
			fb = p.xpath('.//i[contains(@class,"fa-facebook-square")]/parent::a/@href'),
			tw = p.xpath('.//i[contains(@class,"fa-twitter-square")]/parent::a/@href'),
			bl = p.xpath('.//i[contains(@class,"fa-pencil-square")]/parent::a/@href'),
		)
		for k,v in r.items():
			r[k] = "".join(v).strip()
		
		r["name"] = re.sub("[　 ]", "", r["namel"])
		if r["area"].startswith("比例"):
			r["hirei"]=r["area"]
			del(r["area"])
		
		r["url"] = "https://candidates.hr-party.jp/elections/2017/1185/"
		out.writerow([r.get(i) for i in fieldnames])

if __name__=="__main__":
	import sys
	run(sys.stdout)
