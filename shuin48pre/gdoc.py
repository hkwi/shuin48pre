import csv
import re
import xlsxwriter
import unicodedata

def normalize(k,v):
	if v in ("-", ""):
		return k,""
	
	k = {
		"誕生日":"生年月日",
		"選挙用表記名/別名":"候補名",
		"名前（姓）":"姓",
		"名前（名）":"名",
		"公認政党":"政党",
		"担当":None,
		"作業予定日":None,
		"完了日":None,
		"名前（フル）":"名前",
		"名（フリガナ）":"メイ",
		"姓（フリガナ）":"セイ",
		"Twitterアドレス":"twitter",
		"Facebookページアドレス":"facebook",
		"フェイスブックID":"facebook",
		"公式Facebookページ":"facebook",
		"メモ": None
	}.get(k, k)
	
	if k == "twitter":
		v = v.strip().split("?")[0].lower()
		m = re.match("https?://twitter.com/@?([^/@\?]+)", v)
		if m:
			v = m.group(1)
		if v.startswith("\u200E"):
			v = v[1:]
	elif k == "facebook":
		if "?" in v and "id=" not in v:
			v = v.split("?")[0]
		v = v.replace("https://facebook.com/","https://www.facebook.com/")
		v = v.replace("ja-jp.facebook.com","www.facebook.com")
		v = v.replace("http://", "https://")
		if v.startswith("/"):
			v = "https://www.facebook.com" + v
		elif v and not v.startswith("http"):
			v = "https://www.facebook.com/" + v
		
		if v.endswith("/"):
			v = v[:-1]
	elif k == "生年月日":
		m = re.match("(\d{4})(\d{2})(\d{2})", v)
		if m:
			v = "-".join(m.groups())
		m = re.match("(\d+)/(\d+)/(\d+)", v)
		if m:
			v = "%04d-%02d-%02d" % tuple(map(int, m.groups()))
		m = re.match("(\d+)-(\d+)-(\d+)", v)
		if m:
			v = "%04d-%02d-%02d" % tuple(map(int, m.groups()))
	elif k == "性別":
		if not v.endswith("性") and len(v)==1:
			v += "性"
	elif k == "小選挙区":
		v = unicodedata.normalize("NFKC", v.strip())
		m = re.match("^(.*)[県府]\s*(\d+区)$", v)
		if m:
			v = "".join(m.groups())
		m = re.match("^(東京)都\s*(\d+区)$", v)
		if m:
			v = "".join(m.groups())
		v = re.sub("[　 ]+", "", v)
	elif k == "比例区":
		m = re.match("^(比例)?(.*?)(ブロック)?$", v)
		if m:
			v = m.group(2)
		v = {
			"北信越":"北陸信越",
			"九州・沖縄":"九州",
			"東京都":"東京",
		}.get(v, v)
	elif k == "前回":
		if v in ("現職", "現"):
			v = "前"
	elif k == "政党":
		v = {
			"日本維新の会":"維新",
			"希望の党":"希望",
			"自由民主党":"自民",
			"幸福実現党":"幸福",
			"社会民主党":"社民",
			"公明党":"公明",
			"立憲民主党":"立民",
			"立民":"立民",
			"立憲":"立民",
			"立憲民主":"立民",
			"無所":"無所属",
			"日本共産党":"共産",
			"日本のこころ":"こころ",
			"大地":"新党大地",
		}.get(v, v)
	elif k == "前回":
		v = {
			"新人":"新",
		}.get(v, v)
	elif v:
		v = re.sub("[　 ]+", "", v)
	return k,v

def run(fp):
	rows = list(csv.reader(open("docs/gdoc_gray_db.csv")))
	wd = [j for j,r in enumerate(rows) if "wikidata" in r]
	if wd:
		hidx = wd[0]
		skip = hidx+1
		
		rlim = rows[hidx].index("担当")
		header = rows[hidx][:rlim]
		out = csv.writer(fp)
		data = [header]+[[normalize(k,v)[1] for k,v in zip(header, r[:rlim])] for r in rows[skip:]]
		out.writerows(data)
		
		wb = xlsxwriter.Workbook("docs/database.xlsx")
		ws = wb.add_worksheet()
		[[ws.write(i,j,c) for j,c in enumerate(r)] for i,r in enumerate(data)]
		wb.close()

if __name__=="__main__":
	import sys
	run(sys.stdout)
