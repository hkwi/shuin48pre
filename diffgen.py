import io
import re
import csv
import rdflib
import difflib

EX = rdflib.Namespace("http://ns.example.org/")

key_conv = {
	"誕生日":"生年月日",
	"選挙用表記名/別名":"候補名",
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
	for i, r in enumerate(db):
		if "wikidata" in r:
			break
	keys = [key_conv.get(e,e) for e in db[i]] # normalize keys
	return keys, db[i+1:]

def ttl_out(dbkeys, dbdata, keys):
	g = rdflib.Graph()
	for row in sorted(dbdata):
		m = dict([(k,v) for k,v in zip(dbkeys, row) if k])
		name = m.get("候補名",m.get("名前"))
		
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
				m = re.match("(\d{4})/(\d{2})/(\d{2})", v)
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
				objs = list(g.objects(e, EX[k]))
				if objs and not objs[0].value:
					g.set((e, EX[k], rdflib.Literal(v)))
				else:
					g.add((e, EX[k], rdflib.Literal(v)))
	return [l for l in io.StringIO(g.serialize(format="turtle").decode("UTF-8"))]

def gray_to_seijinavi():
	sk, sdb = load_gdoc("docs/gdoc_seiji_navi.csv")
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	
	try:
		flag = gk.index("立候補")
		gdb = [r for r in gdb if r[flag] in ("取りやめ","引退")]
	except ValueError:
		pass
	
	# filter-out
	qnames = [r[sk.index("wikidata")] for r in sdb]
	gdb = [r for r in gdb if r[gk.index("wikidata")] in qnames]

	keys = set(sk).intersection(set(gk))
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(sk, sdb, keys),
		fromfile="GrayDB", tofile="政治ナビ", lineterm='\r\n')
	open("docs/gray_to_seijinavi.diff", "w").writelines(lines)

def gray_to_kyousanto():
	ks = ["候補名",None,"名前","姓","名","せい","めい","年齢",
		"前回", "比例区", "小選挙区", "肩書", "twitter", "facebook", "公式ページ", "メモ"]
	db = [tuple(r) for r in csv.reader(open("docs/kyousanto_official.csv")) if "".join(r)]
	db = list(set(db))
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if r[gk.index("政党")] == "共産"]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="共産党公式", lineterm='\r\n')
	open("docs/gray_to_kyousanto.diff", "w").writelines(lines)

def gray_to_senkyo_dotcom():
	ks1 = ["候補名","名前","姓","名","政党","小選挙区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db1 = [tuple(r) for r in csv.reader(open("docs/senkyo_dotcom.csv")) if "".join(r)]

	ks2 = ["候補名","名前","姓","名","政党","比例区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db2 = [tuple(r) for r in csv.reader(open("docs/senkyo_dotcom_hirei.csv")) if "".join(r)]
	
	ks = ["候補名","名前","姓","名","政党","比例区","小選挙区","前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db = [tuple([dict(zip(ks1, n)).get(k, "") for k in ks]) for n in db1
		] + [tuple([dict(zip(ks2, n)).get(k, "") for k in ks]) for n in db2]
	db = list(set(db))

	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	
	try:
		flag = gk.index("立候補")
		gdb = [r for r in gdb if r[flag] in ("取りやめ","引退")]
	except ValueError:
		pass
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="選挙ドットコム", lineterm='\r\n')
	open("docs/gray_to_senkyo_dotcom.diff", "w").writelines(lines)

def gray_to_ishin():
	ks = ["名前","候補名","ふりがな","前回","小選挙区","比例区","肩書"]
	db = [tuple(r) for r in csv.reader(open("docs/ishin_official.csv")) if "".join(r)]
	db = list(set(db))
	
	ks += ["立候補"]
	db = [r+("党発表",) for r in db]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if r[gk.index("政党")] == "維新"]
	for r in gdb:
		i = gk.index("候補名")
		if not r[i]:
			r[i] = r[gk.index("名前")]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="維新公式", lineterm='\r\n')
	open("docs/gray_to_ishin.diff", "w").writelines(lines)

def gray_to_koumei():
	ks1 = "候補名 小選挙区 twitter facebook youtube line 肩書".split()
	db1 = [tuple(r) for r in csv.reader(open("docs/koumei_official.csv")) if "".join(r)]
	db1 = list(set(db1))
	
	ks2 = "候補名 比例区 twitter facebook youtube line 肩書".split()
	db2 = [tuple(r) for r in csv.reader(open("docs/koumei_official_hirei.csv")) if "".join(r)]
	db2 = list(set(db2))
	
	ks = "候補名 小選挙区 比例区 twitter facebook youtube line 肩書".split()
	db = [tuple([dict(zip(ks1, n)).get(k, "") for k in ks]) for n in db1
		] + [tuple([dict(zip(ks2, n)).get(k, "") for k in ks]) for n in db2]
	db = list(set(db))
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if r[gk.index("政党")] == "公明"]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="公明党公式", lineterm='\r\n')
	open("docs/gray_to_koumei.diff", "w").writelines(lines)


if __name__=="__main__":
	gray_to_seijinavi()
	gray_to_kyousanto()
	gray_to_senkyo_dotcom()
	gray_to_ishin()
	gray_to_koumei()
