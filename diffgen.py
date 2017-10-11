import io
import re
import csv
import rdflib
import difflib
import unicodedata
import jaconv

EX = rdflib.Namespace("http://ns.example.org/")

key_conv = {
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
	
	if "立候補" in keys:
		flag = keys.index("立候補")
		db = [r for r in db if r[flag] not in ("取りやめ","引退", "不出馬")]
	
	if "候補名" in keys:
		for r in db:
			if not r[keys.index("候補名")]:
				r[keys.index("候補名")] = r[keys.index("名前")]
	if "かな" in keys:
		if "よみがな" not in keys:
			keys += ["よみがな"]
			db = [r+[re.sub("[　 ]+","",r[keys.index("かな")])] for r in db]
		if "せい" not in keys and "めい" not in keys:
			keys += ["せい","めい"]
			ndb = []
			for j,r in enumerate(db):
				seimei = re.split("[　 ]+", jaconv.kata2hira(r[keys.index("かな")]))
				if j>i and len(seimei)==2:
					ndb += [r + seimei]
				else:
					ndb += [r + ["",""]]
			db = ndb
	return keys, db[i+1:]

def match_names(keys, row):
	r = dict(zip(keys, row))
	for k in "せい めい よみがな".split():
		if k in keys:
			r[k] = jaconv.kata2hira(r[k])
		kata = jaconv.hira2kata(k)
		if kata in keys:
			r[jaconv.kata2hira(k)] = jaconv.kata2hira(r[kata])
	names = []
	for fields in "名前 候補名 姓+名 姓+めい せい+めい せい+名 よみがな".split():
		nm = ""
		for field in fields.split("+"):
			if r.get(field):
				nm += r[field]
			else:
				nm = None
				break
		if nm is not None:
			names += [nm]
	
	return names

def create_mkey(a, b):
	'''create a key list, filtered with b key'''
	mkeys = []
	for ak in a:
		search = []
		for bk in b:
			xs = set(ak).intersection(bk)
			search += [(len(xs), xs)]
		hi = next(reversed(sorted(search)))
		if hi[0] > 0:
			mkeys += [next(reversed(sorted(hi[1])))]
		else:
			mkeys += [None]
	return mkeys

def ttl_out(dbkeys, dbdata, keys):
	g = rdflib.Graph()
	bnodes = {}
	for row in dbdata:
		m = dict([(k,v) for k,v in zip(dbkeys, row) if k])
		for k in reversed("mkey 候補名 名前".split()):
			nm = m.get(k)
			if nm:
				name = nm
		
		if "mkey" in m:
			del(m["mkey"])
		
		e = bnodes.get(name, rdflib.BNode(name))
		bnodes[name] = e
		for k,vs in m.items():
			for v in vs.split("\n"):
				if k == "twitter":
					v = v.strip().split("?")[0].lower()
					m = re.match("https?://twitter.com/@?([^/]+)(/.*)?", v)
					if m:
						v = m.group(1)
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
					v = unicodedata.normalize("NFKC", v)
					m = re.match("(.*)[県府]\s*(\d+区)", v)
					if m:
						v = "".join(m.groups())
					m = re.match("(東京)都\s*(\d+区)", v)
					if m:
						v = "".join(m.groups())
					v = re.sub("[　 ]+", "", v)
				elif k == "比例区":
					m = re.match("^(比例)?(.*?)(ブロック)?$", v)
					if m:
						v = m.group(2)
					v = {
						"北陸信越":"北信越",
						"九州・沖縄":"九州",
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
						"立憲民主党":"立憲民主",
						"立民":"立憲民主",
						"立憲":"立憲民主",
						"無所":"無所属",
						"日本共産党":"共産",
					}.get(v, v)
				elif k == "前回":
					v = {
						"新人":"新",
					}.get(v, v)
				elif v:
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
	ks, db = load_gdoc("docs/gdoc_seiji_navi.csv")
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	
	# filter-out
	qnames = [r[ks.index("wikidata")] for r in db]
	gdb = [r for r in gdb if r[gk.index("wikidata")] in qnames]

	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(set(gk))
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="政治ナビ", lineterm='\r\n')
	open("docs/gray_to_seijinavi.diff", "w").writelines(lines)

def gray_to_kyousanto():
	ks = ["候補名",None,"名前","姓","名","せい","めい","年齢",
		"前回", "比例区", "小選挙区", "肩書", "twitter", "facebook", "公式ページ", "メモ"]
	db = [r for r in csv.reader(open("docs/kyousanto_official.csv")) if "".join(r)]
	db = [list(r) for r in set([tuple(r) for r in db])]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "共産" in r[gk.index("政党")]]
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
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
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
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
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
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
	db = [list(r) for r in set([tuple(r) for r in db])]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "公明" in r[gk.index("政党")]]
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
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
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(gk)
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="自民党公式", lineterm='\r\n')
	open("docs/gray_to_jimin.diff", "w").writelines(lines)

def gray_to_ritsumin():
	ks1 = "小選挙区 名前 前回 立候補".split()
	db1 = [r+["党発表"] for r in csv.reader(open("docs/ritsumin_media.csv")) if not is_empty(r)]
	ks2 = "公認 小選挙区 比例区 名前 前回 立候補".split()
	db2 = [r+["党発表"] for r in csv.reader(open("docs/ritsumin_media2.csv")) if not is_empty(r)]
	ks = "公認 小選挙区 比例区 名前 前回 立候補".split()
	db = [[dict(zip(ks1,r)).get(k,"") for k in ks] for r in db1
		] + [[dict(zip(ks2,r)).get(k,"") for k in ks] for r in db2 ]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "立民" in r[gk.index("政党")]]
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="立憲民主（報道）", lineterm='\r\n')
	open("docs/gray_to_ritsumin.diff", "w").writelines(lines)

def gray_to_koufuku():
	ks = ["候補名",None]+"よみ 小選挙区 比例区 facebook twitter 公式ブログ 職歴 立候補".split()
	db = [r+["党発表"] for r in csv.reader(open("docs/koufuku_official.csv")) if not is_empty(r)]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "幸福" in r[gk.index("政党")]]
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="幸福公式", lineterm='\r\n')
	open("docs/gray_to_koufuku.diff", "w").writelines(lines)

def gray_to_kibou():
	ks = "小選挙区 比例区 メモ 候補名".split()+ [None, "立候補"]
	db = [r+["党発表"] for r in csv.reader(open("docs/kibou_media2.csv")) if not is_empty(r)]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	gdb = [r for r in gdb if "希望" in r[gk.index("政党")] or "民進" in r[gk.index("政党")]]
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="希望（報道）", lineterm='\r\n')
	open("docs/gray_to_kibou.diff", "w").writelines(lines)

def gray_to_asahi():
	ks = ["小選挙区","比例区",None,None,"姓","名","せい","めい","年齢","政党","推薦",None, None, None,"経歴"]
	ks = ["小選挙区","比例区",None,None,"姓","名","せい","めい",None,"政党","推薦",None, None, None,"経歴"]
	db = [r for r in csv.reader(open("docs/asahi.csv")) if not is_empty(r)]
	ks += ["名前"]
	db = [r+[r[ks.index("姓")]+r[ks.index("名")]] for r in db]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db.csv")
	
	kname = [match_names(ks,r) for r in db]
	gname = [match_names(gk,r) for r in gdb]
	ks += ["mkey"]
	db = [r+[nm] for r,nm in zip(db,create_mkey(kname, gname))]
	gk += ["mkey"]
	gdb = [r+[nm] for r,nm in zip(gdb,create_mkey(gname, kname))]
	
	keys = set(ks).intersection(set(gk))
	
	lines = difflib.unified_diff(ttl_out(gk, gdb, keys),
		ttl_out(ks, db, keys),
		fromfile="GrayDB", tofile="朝日.com", lineterm='\r\n')
	open("docs/gray_to_asahi.diff", "w").writelines(lines)


if __name__=="__main__":
	gray_to_seijinavi()
	gray_to_kyousanto()
	gray_to_senkyo_dotcom()
	gray_to_ishin()
	gray_to_koumei()
	gray_to_jimin()
	gray_to_ritsumin()
	gray_to_koufuku()
	gray_to_kibou()
	gray_to_asahi()
