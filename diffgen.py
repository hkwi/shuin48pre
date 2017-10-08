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

def is_empty(row):
	s = "".join(row)
	if not s or s.startswith("※"):
		return True
	return False

def load_gdoc(filename):
	db = [r for r in csv.reader(open(filename)) if "".join(r)]
	for i, r in enumerate(db):
		if "wikidata" in r:
			break
	keys = [key_conv.get(e,e) for e in db[i]] # normalize keys
	if "候補名" in keys:
		for r in db:
			if not r[keys.index("候補名")]:
				r[keys.index("候補名")] = r[keys.index("名前")]
	return keys, db[i+1:]

def ttl_out(dbkeys, dbdata, keys):
	g = rdflib.Graph()
	bnodes = {}
	for row in dbdata:
		m = dict([(k,v) for k,v in zip(dbkeys, row) if k])
		name = m.get("候補名",m.get("名前"))
		
		e = bnodes.get(name, rdflib.BNode(name))
		bnodes[name] = e
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
				v = re.sub("[　 ]+", "", v)
			
			if k in keys:
				objs = list(g.objects(e, EX[k]))
				if len(objs) == 0:
					g.add((e, EX[k], rdflib.Literal(v)))
				elif v:
					if "".join([o.value for o in objs]):
						g.add((e, EX[k], rdflib.Literal(v)))
					else:
						g.set((e, EX[k], rdflib.Literal(v)))
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
	ks = ["名前",None,"候補名","姓","名","せい","めい","年齢",
		"前回", "比例区", "小選挙区", "肩書", "twitter", "facebook", "公式ページ", "メモ"]
	db = [r for r in csv.reader(open("docs/kyousanto_official.csv")) if "".join(r)]
	db = [list(r) for r in set([tuple(r) for r in db])]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "共産" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="共産党公式", lineterm='\r\n')
	open("docs/gray_to_kyousanto.diff", "w").writelines(lines)

def gray_to_senkyo_dotcom():
	ks1 = ["名前","候補名","姓","名","政党","小選挙区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db1 = [r for r in csv.reader(open("docs/senkyo_dotcom.csv")) if "".join(r)]

	ks2 = ["名前","候補名","姓","名","政党","比例区", "前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db2 = [r for r in csv.reader(open("docs/senkyo_dotcom_hirei.csv")) if "".join(r)]
	
	ks = ["名前","候補名","姓","名","政党","比例区","小選挙区","前回","年齢",
		"twitter","facebook","公式サイト","肩書","年齢（歳付き）"]
	db = [[dict(zip(ks1, n)).get(k, "") for k in ks] for n in db1
		] + [[dict(zip(ks2, n)).get(k, "") for k in ks] for n in db2]
	for r in db:
		tw = ks.index("twitter")
		if r[tw] and r[tw].startswith("https://twitter.com/"):
			r[tw] = r[tw][len("https://twitter.com/"):]
	db = [list(r) for r in set([tuple(r) for r in db])]

	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	try:
		flag = gk.index("立候補")
		gdb = [r for r in gdb if r[flag] not in ("取りやめ","引退")]
	except ValueError:
		pass
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="選挙ドットコム", lineterm='\r\n')
	open("docs/gray_to_senkyo_dotcom.diff", "w").writelines(lines)

def gray_to_ishin():
	ks = "名前 候補名 ふりがな 前回 小選挙区 比例区 肩書 党発表".split()
	db = [r+["立候補"] for r in csv.reader(open("docs/ishin_official.csv")) if "".join(r)]
	db = [list(r) for r in set([tuple(r) for r in db])]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "維新" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="維新公式", lineterm='\r\n')
	open("docs/gray_to_ishin.diff", "w").writelines(lines)

def gray_to_koumei():
	ks1 = "候補名 小選挙区 twitter facebook youtube line 肩書".split()
	db1 = [r for r in csv.reader(open("docs/koumei_official.csv")) if "".join(r)]
	
	ks2 = "候補名 比例区 twitter facebook youtube line 肩書".split()
	db2 = [r for r in csv.reader(open("docs/koumei_official_hirei.csv")) if "".join(r)]
	
	ks = "候補名 小選挙区 比例区 twitter facebook youtube line 肩書".split()
	db = [[dict(zip(ks1, n)).get(k, "") for k in ks] for n in db1
		] + [[dict(zip(ks2, n)).get(k, "") for k in ks] for n in db2]
	for r in db:
		tw = ks.index("twitter")
		m = re.match("https?://twitter.com/([^/]+)(/.*)?", r[tw])
		if m:
			r[tw] = m.group(1)
	db = [list(r) for r in set([tuple(r) for r in db])]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "公明" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="公明党公式", lineterm='\r\n')
	open("docs/gray_to_koumei.diff", "w").writelines(lines)

def gray_to_jimin():
	ks = "小選挙区 比例区 立候補 推薦 姓 名 せい めい 性別 誕生日 肩書 職歴 候補名".split()
	db = [r+[r[ks.index("姓")]+r[ks.index("名")]] for r in csv.reader(open("docs/jimin_official.csv")) if "".join(r)]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "自民" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="自民党公式", lineterm='\r\n')
	open("docs/gray_to_jimin.diff", "w").writelines(lines)

def gray_to_ritsumin():
	ks = "小選挙区 名前 前回 立候補".split()
	db = [r+["党発表"] for r in csv.reader(open("docs/ritsumin_media.csv")) if not is_empty(r)]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "立民" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="立憲民主（報道）", lineterm='\r\n')
	open("docs/gray_to_ritsumin.diff", "w").writelines(lines)

def gray_to_koufuku():
	ks = ["候補名",None]+"よみ 小選挙区 比例区 facebook twitter 公式サイト 職歴 立候補".split()
	db = [r+["党発表"] for r in csv.reader(open("docs/koufuku_official.csv")) if not is_empty(r)]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "幸福" in r[gk.index("政党")]]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="幸福公式", lineterm='\r\n')
	open("docs/gray_to_koufuku.diff", "w").writelines(lines)


if __name__=="__main__":
	gray_to_seijinavi()
	gray_to_kyousanto()
	gray_to_senkyo_dotcom()
	gray_to_ishin()
	gray_to_koumei()
	gray_to_jimin()
	gray_to_ritsumin()
	gray_to_koufuku()
