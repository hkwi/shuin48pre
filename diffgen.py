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

seiji_navi = load_gdoc("docs/gdoc_seiji_navi.csv")
gray_db = load_gdoc("docs/gdoc_gray_db.csv")

keys = set(seiji_navi[0]).intersection(set(gray_db[0]))
names = set([row[seiji_navi[0].index("名前")] for row in seiji_navi[1]]).intersection(
	[row[gray_db[0].index("名前")] for row in gray_db[1]])

def ttl_out(db):
	g = rdflib.Graph()
	for row in sorted(db[1]):
		m = dict([(k,v) for k,v in zip(db[0], row) if k])
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
			
			if k in keys:
				g.add((e, EX[k], rdflib.Literal(v)))
	return [l for l in io.StringIO(g.serialize(format="turtle").decode("UTF-8"))]

lines = difflib.unified_diff(ttl_out(gray_db), ttl_out(seiji_navi),
		fromfile="GrayDB", tofile="政治ナビ", lineterm='\r\n')
open("docs/gray_to_seijinavi.diff", "w").writelines(lines)
