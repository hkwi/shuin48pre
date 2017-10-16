# coding: UTF-8
#
# 共産党 公式ウェブサイト
#
import re
import sys
import csv
import lxml.html
import unicodedata

urls = ["http://www.jcp.or.jp/web_senkyo/cat1/"]
urls += ["http://www.jcp.or.jp/web_senkyo/cat1/index_%d.html" % s for s in range(2,8)]
urls += ["http://www.jcp.or.jp/web_senkyo/cat/"]
urls += ["http://www.jcp.or.jp/web_senkyo/cat/index_%d.html" % s for s in (2,3)]

fieldnames="koho_namel koho_kana name family_name given_name family_hira given_hira age flag block small koho_kata twitter facebook site syubetsu url".split()

def hiragana_split(s):
	if s=="四ツ谷":
		return ["", s]
	
	ret = [""]
	hiragana = True
	for c in s:
		nm = unicodedata.name(c)
		n = nm.startswith("HIRAGANA") or nm.startswith("KATAKANA")
		if n:
			if hiragana:
				ret[-1] += c
			else:
				hiragana = True
				ret.append(c)
		else:
			if hiragana:
				hiragana = False
				ret.append(c)
			else:
				ret[-1] += c
	return ret

def run(fp):
	out = csv.writer(fp)
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
			
			# convert senkyo_ku to (block, small)
			if "重複" in row.get("syubetsu", ""):
				ab = row["senkyo_ku"].split("、", 1)
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
			
			# convert koho_agen
			if "koho_agen" in row:
				pt = unicodedata.normalize("NFKC", row["koho_agen"])
				m = re.match("\(\s*(\d+)\s*\)(.*)", pt.strip())
				assert m, pt
				row["age"] = m.group(1)
				row["flag"] = m.group(2)
				del(row["koho_agen"])
			
			# pump names
			n1 = re.split("[ 　]", row["koho_namel"])
			n2 = re.split("[ 　]", row.get("koho_kana", ""))
			if len(n1)==2 and len(n2)==2:
				t1 = hiragana_split(n1[0])
				t2 = hiragana_split(n2[0])
				t = t1[1::2] + t2[1::2]
				nokana = "".join(t[::2] + t[1::2])
				t = t1[::2] + t2[::2]
				kana = "".join(t[::2] + t[1::2])
				if nokana and kana:
					row["family_name"] = nokana
					row["family_hira"] = kana
				elif kana:
					row["family_name"] = "".join(t[::2])
					row["family_hira"] = "".join(t[::2])
				
				t1 = hiragana_split(n1[1])
				t2 = hiragana_split(n2[1])
				t = t1[1::2] + t2[1::2]
				nokana = "".join(t[::2] + t[1::2])
				t = t1[::2] + t2[::2]
				kana = "".join(t[::2] + t[1::2])
				if nokana and kana:
					row["given_name"] = nokana
					row["given_hira"] = kana
				elif kana:
					row["given_name"] = "".join(t[::2])
					row["given_hira"] = "".join(t[::2])
				
				row["name"] = row["family_name"]+row["given_name"]
			else:
				row["name"] = row["koho_namel"]
			
			row["url"] = url
			out.writerow([row.get(f) for f in fieldnames])

if __name__=="__main__":
	import sys
	run(sys.stdout)
