import io
import re
import csv
import rdflib
import difflib

EX = rdflib.Namespace("http://ns.example.org/")

key_conv = {
	"誕生日":"生年月日",
	"担当":None,
	"作業予定日":None,
	"完了日":None,
	"名（フリガナ）":"メイ",
	"姓（フリガナ）":"セイ",
	"Twitterアドレス":"twitter",
	"Facebookページアドレス":"facebook",
	"メモ": None
}

def load_gdoc(filename):
	db = [r for r in csv.reader(open(filename)) if "".join(r)]
	i = [r[0] for r in db].index("wikidata")
	keys = [key_conv.get(e,e) for e in db[i]] # normalize keys
	return keys, db[i+1:]

def ttl_out(dbkeys, dbdata, keys, names):
	g = rdflib.Graph()
	for row in sorted(dbdata):
		m = dict([(k,v) for k,v in zip(dbkeys, row) if k])
		name = m["名前"]
		if name not in names:
			continue
		e = rdflib.BNode(name)
		for k,v in m.items():
			if k == "twitter":
				v = v.split("?")[0].lower()
			elif k == "facebook":
				v = v.replace("https://facebook.com/","https://www.facebook.com/")
			elif k == "生年月日":
				m = re.match("(\d{4})(\d{2})(\d{2})", v)
				if m:
					v = "-".join(m.groups())
			elif k == "性別":
				if not v.endswith("性") and len(v)==1:
					v += "性"
			elif k == "小選挙区":
				m = re.match("(.*)[県府]\s*(\d+区)", v)
				if m:
					v = "".join(m.groups())
				m = re.match("(東京)都\s*(\d+区)", v)
				if m:
					v = "".join(m.groups())
			
			if k in keys:
				g.add((e, EX[k], rdflib.Literal(v)))
	return [l for l in io.StringIO(g.serialize(format="turtle").decode("UTF-8"))]

def gray_to_seijinavi():
	seiji_navi = load_gdoc("docs/gdoc_seiji_navi.csv")
	gray_db = load_gdoc("docs/gdoc_gray_db.csv")

	keys = set(seiji_navi[0]).intersection(set(gray_db[0]))
	names = set([row[seiji_navi[0].index("名前")] for row in seiji_navi[1]]).intersection(
		[row[gray_db[0].index("名前")] for row in gray_db[1]])

	lines = difflib.unified_diff(ttl_out(gray_db[0], gray_db[1], keys, names),
		ttl_out(seiji_navi[0], seiji_navi[1], keys, names),
		fromfile="GrayDB", tofile="政治ナビ", lineterm='\r\n')
	open("docs/gray_to_seijinavi.diff", "w").writelines(lines)

def gray_to_kyousanto():
	ks = ["候補名",None,"名前","姓","名","せい","めい","年齢",
		"前回", "比例区", "小選挙区", "肩書", "twitter", "facebook", "公式ページ", "メモ"]
	db = [tuple(r) for r in csv.reader(open("docs/kyousanto_official.csv")) if "".join(r)]
	db = list(set(db))
	gray_db = load_gdoc("docs/gdoc_gray_db.csv")
	
	keys = set(ks).intersection(set(gray_db[0]))
	names = set([row[ks.index("名前")] for row in db]).intersection(
		[row[gray_db[0].index("名前")] for row in gray_db[1]])
	
	lines = difflib.unified_diff(ttl_out(gray_db[0], gray_db[1], keys, names),
		ttl_out(ks, db, keys, names),
		fromfile="GrayDB", tofile="共産党公式", lineterm='\r\n')
	open("docs/gray_to_kyousanto.diff", "w").writelines(lines)

def gray_to_senkyo_dotcom():
	ks = ["候補名","名前","姓","名","政党","小選挙区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db = [tuple(r) for r in csv.reader(open("docs/senkyo_dotcom.csv")) if "".join(r)]
	db = list(set(db))
	gray_db = load_gdoc("docs/gdoc_gray_db.csv")
	
	keys = set(ks).intersection(set(gray_db[0]))
	names = set([row[ks.index("名前")] for row in db]).intersection(
		[row[gray_db[0].index("名前")] for row in gray_db[1]])
	
	lines = difflib.unified_diff(ttl_out(gray_db[0], gray_db[1], keys, names),
		ttl_out(ks, db, keys, names),
		fromfile="GrayDB", tofile="選挙ドットコム", lineterm='\r\n')
	open("docs/gray_to_senkyo_dotcom.diff", "w").writelines(lines)

def gray_to_senkyo_dotcom_hirei():
	ks = ["候補名","名前","姓","名","政党","比例区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db = [tuple(r) for r in csv.reader(open("docs/senkyo_dotcom.csv")) if "".join(r)]
	db = list(set(db))
	gray_db = load_gdoc("docs/gdoc_gray_db.csv")
	
	keys = set(ks).intersection(set(gray_db[0]))
	names = set([row[ks.index("名前")] for row in db]).intersection(
		[row[gray_db[0].index("名前")] for row in gray_db[1]])
	
	lines = difflib.unified_diff(ttl_out(gray_db[0], gray_db[1], keys, names),
		ttl_out(ks, db, keys, names),
		fromfile="GrayDB", tofile="選挙ドットコム（比例）", lineterm='\r\n')
	open("docs/gray_to_senkyo_dotcom_hirei.diff", "w").writelines(lines)

gray_to_seijinavi()
gray_to_kyousanto()
gray_to_senkyo_dotcom()
gray_to_senkyo_dotcom_hirei()
