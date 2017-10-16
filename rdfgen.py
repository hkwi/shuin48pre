import io
import re
import csv
import rdflib
import unicodedata
import jaconv
import sys

ns = dict(
	wd= "http://www.wikidata.org/entity/",
	wdt= "http://www.wikidata.org/prop/direct/",
	rdfs= "http://www.w3.org/2000/01/rdf-schema#",
	p= "http://www.wikidata.org/prop/",
	pr= "http://www.wikidata.org/prop/reference/",
	ps= "http://www.wikidata.org/prop/statement/",
	psv= "http://www.wikidata.org/prop/statement/value/",
	prov= "http://www.w3.org/ns/prov#",
)
for k,v in ns.items():
	globals()[k.upper()] = rdflib.Namespace(v)

def new_graph():
	g = rdflib.Graph()
	for k,v in ns.items():
		g.bind(k, rdflib.Namespace(v))
	return g

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
	"フェイスブックID":"facebook",
	"公式Facebookページ":"facebook",
	"メモ": None
}

def is_empty(row):
	s = "".join(row)
	if not s or s.startswith("※"):
		return True
	return False

def load_gdoc(filename):
	db = [r for r in csv.reader(open(filename, encoding="UTF-8")) if "".join(r)]
	for i, r in enumerate(db):
		if "wikidata" in r:
			break
	keys = [key_conv.get(e,e) for e in db[i]] # normalize keys
	if "GrayDBId" in keys:
		left = keys.index("GrayDBId")
		keys = keys[:left]
		db = [r[:left] for r in db]
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
				k,v = normalize(field, r[field])
				nm += v
			else:
				nm = None
				break
		if nm is not None:
			names += [nm]
	
	if r.get("twitter"):
		k,v = normalize("twitter", r["twitter"])
		names += ["twitter://"+v.lower()]
	
	return names

def fetch_key_with_data(akeys, bkeys, bdata, default_key=None):
	'''create a key list, filtered with b key'''
	xkey_w_bdata = []
	for ak in akeys:
		search = []
		for bk,fr in zip(bkeys, bdata):
			xs = set(ak).intersection(bk)
			search += [(len(xs), xs, fr)]
		hi = next(reversed(sorted(search)))
		if hi[0] > 0:
			heavy_key = next(reversed(sorted(hi[1])))
			found = [heavy_key, hi[2]]
		else:
			found = [default_key, [None]*len(fr)]
		
		xkey_w_bdata += [found]
	return xkey_w_bdata

def normalize(k,v):
	if v == "-":
		return k,""
	
	k = key_conv.get(k,k)
	if k == "twitter":
		v = v.strip().split("?")[0].lower()
		m = re.match("https?://twitter.com/@?([^/@\?]+)", v)
		if m:
			v = m.group(1)
		if v.startswith("\u200E"):
			v = v[1:]
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
			"立憲民主党":"立憲民主",
			"立民":"立憲民主",
			"立憲":"立憲民主",
			"無所":"無所属",
			"日本共産党":"共産",
			"日本のこころ":"こころ",
			"新党大地":"大地",
		}.get(v, v)
	elif k == "前回":
		v = {
			"新人":"新",
		}.get(v, v)
	elif v:
		v = re.sub("[　 ]+", "", v)
	return k,v

def asahi_rdf():
	ks = ["小選挙区","比例区","順序",None,"姓","名","せい","めい","年齢","政党","推薦",None,None,None,None,"url"]
	db = [r for r in csv.reader(open("docs/asahi.csv", encoding="UTF-8")) if not is_empty(r)]
	db = [[normalize(k,v.strip())[1] for k,v in zip(ks,r)] for r in db]
	db = [r for r in db if r[ks.index("比例区")]]
	ks += ["名前"]
	db = [r+[r[ks.index("姓")]+r[ks.index("名")]] for r in db]
	
	gk, gdb = load_gdoc("docs/gdoc_gray_db_0.csv")
	gdb = [[normalize(k,v.strip())[1] for k,v in zip(gk,r)] for r in gdb]
	
	kname = [[(n,r[ks.index("政党")]) for n in match_names(ks,r)] for r in db]
	gname = [[(n,r[gk.index("政党")]) for n in match_names(gk,r)] for r in gdb]
	
	ks += ["xname", "xparty"] + ["remote_%s" % k for k in gk]
	db = [r+list(remote[0])+remote[1] for r,remote in zip(db, fetch_key_with_data(kname, gname, gdb, default_key=(None,None)))]
	
	g = new_graph()
	for r in db:
		assert r[ks.index("remote_wikidata")]
		person = WD[r[ks.index("remote_wikidata")]]
		g.add((person, RDFS.label, rdflib.Literal(r[ks.index("名前")], lang="ja")))
		
		# 立候補選挙
		st = rdflib.BNode()
		g.add((person, P["P3602"], st))
		g.add((st, PR["P3602"], WD["Q20983100"]))
		ref = rdflib.BNode()
		g.add((st, PROV.wasDerivedFrom, ref))
		g.add((ref, PR["P854"], rdflib.URIRef(r[ks.index("url")])))
		
		# P854 よみがな
		if r[ks.index("せい")] and r[ks.index("めい")]:
			n = rdflib.BNode()
			g.add((person, P["P1814"], n))
			g.add((n, PS["P1814"],
				rdflib.Literal("%s %s" % (r[ks.index("せい")], r[ks.index("めい")]))))
			# I don't know why not set lang=ja here
			
			ref = rdflib.BNode()
			g.add((n, PROV.wasDerivedFrom, ref))
			g.add((ref, PR["P854"], rdflib.URIRef(r[ks.index("url")])))
	
	g.serialize(destination=open("docs/asahi.ttl","wb"), format="turtle")

if __name__=="__main__":
	asahi_rdf()
