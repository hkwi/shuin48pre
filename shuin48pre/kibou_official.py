import yaml
import io
import lxml.html
import urllib.parse
import requests

def urlopen(url):
	return io.StringIO(requests.get(url).content.decode("UTF-8"))

def run(fp):
	fieldnames = "name area twitter facebook youtube line bio".split()
	
	urls = ["https://kibounotou.jp/election/lists/bid:%d" % i for i in range(1,12)]
	for url in urls:
		d = lxml.html.parse(urlopen(url))
		block = d.xpath(".//h3")
		for b in block:
			for n in b.xpath("./following-sibling::*"):
				for p in n.xpath(".//li"):
					ds = p.xpath("./a/@href")
					assert len(ds) == 1
					url2 = urllib.parse.urljoin(url, ds[0])
					
					pd = lxml.html.parse(urlopen(url2))
					lis = pd.xpath('.//*[@class="inner"]//dd//li')
					p = lis[0]
					r = dict(
						name= p.xpath('.//*[@class="name"]/text()'),
						kana= p.xpath('.//*[@class="name"]/span/text()'),
						pos = p.xpath('.//*[@class="position"]/text()'),
						block_name = b.xpath(".//text()"),
					)
					for k,vs in r.items():
						v = " ".join([v.strip() for v in vs if v.strip()])
						r[k] = "\n".join([r.strip() for r in v.split("\n") if r.strip()])
					
					opts = []
					for s in lis[1:]:
						opt = dict(
							title = s.xpath('.//*[@class="title"]//text()'),
							val = s.xpath('.//*[@class="str"]//text()'),
						)
						for k,vs in opt.items():
							opt[k] = " ".join([v.strip() for v in vs if v.strip()])
						opts.append(opt)
					
					r["opts"] = opts
					
					yaml.dump(r, stream=fp,
						explicit_start=True,
						default_flow_style=False,
						allow_unicode=True)

if __name__=="__main__":
	import sys
	run(sys.stdout)
