import urllib.request
import lxml.html
import csv
import re

def run(fp):
	fieldnames = ["namel","name","hira","prev","area1","area2", "bio"]
	
	out = csv.writer(fp)
	d = lxml.html.parse(urllib.request.urlopen("https://o-ishin.jp/election/candidate/2017-3/"))
	for p in d.xpath('.//section[@class="member01"]/div'):
		r = dict(
			namel = p.xpath('.//dt/text()'),
			hira = p.xpath('.//dt/span/text()'),
			prev = p.xpath('.//li[@class="member_label02"]/text()'),
			area = p.xpath('.//li[@class="member_label04"]/text()'),
			bio = p.xpath('.//li[@class="block"]/text()'),
		)
		for k,v in r.items():
			r[k] = "".join(v).strip()
		
		r["name"] = re.sub("[　 ]", "", r["namel"])
		
		if r["area"].endswith("ブロック"):
			r["area2"]=r["area"]
		else:
			r["area1"]=r["area"]
		out.writerow([r.get(i) for i in fieldnames])

if __name__=="__main__":
	import sys
	run(sys.stdout)
