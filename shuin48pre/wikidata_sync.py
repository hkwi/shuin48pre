import re
import rdflib
import csv
import os.path
import itertools
import urllib.parse
import logging

ns={}
for k,v in csv.reader(open(os.path.join(os.path.dirname(__file__), "ns.csv"))):
	globals()[k.upper()] = rdflib.Namespace(v)
	ns[k] = v

def properties(fp):
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	kv = dict(
		kana= "P1814",
		born= "P569",
		photo= "P18",
		twitter= "P2002",
		facebook= "P2013",
		youtube= "P2397",
		site= "P856",
		email= "P968",
		blog= "P1581",
		detail= "P973",
		gender= "P21",
	)
	opts = "\n".join(["OPTIONAL { ?p wdt:%s ?%s . }" % (v,k)
		for k,v in kv.items()])
	res = w.query('''
	SELECT * WHERE {
		?p wdt:P3602 wd:Q20983100 .
		%s
	}
	''' % opts)
	wd = rdflib.Graph()
	for r in res:
		for k,v in kv.items():
			if r[k]:
				wd.add((r["p"], WDT[v], r[k]))
	
	twitter_sn_conv = {r["asis"]:r["screen_name"] for r
		in csv.DictReader(open("docs/twitter_sn_map.csv"))}
	
	gd = rdflib.Graph()
	fields = None
	for r in csv.reader(open("docs/gdoc_gray_db.csv")):
		if fields is None:
			if "wikidata" in r:
				for k in "wikidata 性別 誕生日".split():
					assert k in r, r
				fields = r
			continue
		if not "".join(r):
			continue
		
		qname = r[fields.index("wikidata")]
		if not qname:
			continue
		
		s = WD[qname]
		
		for v in r[fields.index("かな")].split("\n"):
			gd.add((s, WDT["P1814"], rdflib.Literal(v)))
		
		gd.add((s, WDT["P21"], {
			"男": WD["Q6581097"],
			"女": WD["Q6581072"],
		}[r[fields.index("性別")][0]]))
		
		v = r[fields.index("誕生日")]
		v = "%04d-%02d-%02dT00:00:00+00:00" % tuple(map(int,re.split("[/-]", v)))
		gd.add((s, WDT["P569"], rdflib.Literal(v, datatype=rdflib.XSD.dateTime)))
		
		for v in r[fields.index("twitter")].split("\n"):
			v = v.strip()
			m = re.match("https?://(www.)twitter.com/[@＠]?([^@/\?]+)", v)
			if m:
				v = m.group(2)
			if v and v!="-":
				v2 = twitter_sn_conv.get(v, v)
				if v2 and v2 != "-":
					gd.add((s, WDT["P2002"], rdflib.Literal(v2)))
				else:
					logging.warn("twitter ID conversion error %s" % v)
		
		for v in r[fields.index("公式ブログ")].split("\n"):
			if v and v!="-":
				gd.add((s, WDT["1581"], rdflib.Literal(v.strip())))
		
		for v in r[fields.index("公式サイト")].split("\n"):
			if v and v!="-":
				gd.add((s, WDT["P856"], rdflib.Literal(v.strip())))
	
	for r in csv.DictReader(open("docs/fb.csv")):
		if r["dst"] == "-":
			continue
		pc = urllib.parse.urlparse(r["dst"])
		if pc.path == "/profile.php":
			rep = urllib.parse.parse_qs(pc.query)["id"][0]
		else:
			rep = urllib.parse.unquote(pc.path).split("/")[1]
		gd.add((WD[r["qname"]], WDT["P2013"], rdflib.Literal(rep)))
	
	out = csv.writer(fp)
	out.writerow("db person property value".split())
	for s in sorted(set(gd.subjects())-set(wd.subjects())):
		out.writerow(("ours", s[len(WD):], "", ""))
	for s in sorted(set(wd.subjects())-set(gd.subjects())):
		out.writerow(("wikidata", s[len(WD):], "", ""))
	
	for p in sorted(set(itertools.chain(gd.predicates(), wd.predicates()))):
		for s in sorted(set(gd.subjects())):
			w = set(wd.objects(s, p))
			g = set(gd.objects(s, p))
			for o in sorted(g-w):
				out.writerow(("ours", s[len(WD):], p[len(WDT):], o))
			for o in sorted(w-g):
				out.writerow(("wikidata", s[len(WD):], p[len(WDT):], o))

def qualifiers(fp):
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
	  ?person p:P3602 ?st .
	  ?st ps:P3602 wd:Q20983100 .
	  OPTIONAL { ?st pq:P768 ?area . }
	  OPTIONAL { ?st pq:P1268 ?party . }
	}
	''')
	ks = "person area party".split()
	wd = [[r[k][len(WD):] if r[k] else "" for k in ks] for r in res]
	wd = set([tuple(r) for r in wd])

	area_lut = dict(csv.reader(open("docs/areas.csv")))
	party_lut = dict(csv.reader(open("docs/parties.csv")))
	g = csv.reader(open("docs/gdoc_gray_db.csv"))
	gd = []
	fields = None
	for r in g:
		if fields is None:
			if "wikidata" in r:
				for k in "wikidata 公認政党 比例区 小選挙区".split():
					assert k in r, r
				fields = r
			continue
		if not "".join(r):
			continue
		
		qname = r[fields.index("wikidata")]
		party = party_lut[r[fields.index("公認政党")]]
		area = r[fields.index("小選挙区")]
		if area:
			area = area_lut[area.replace(" ","第")]
			gd.append((qname, area, party))
		
		area = r[fields.index("比例区")]
		if area:
			area = area_lut["比例%sブロック" % area]
			gd.append((qname, area, party))

	gd = set(gd)
	
	out = csv.writer(fp)
	out.writerow("db person area party".split())
	out.writerows([("ours",)+r for r in sorted(gd-wd)])
	out.writerows([("wikidata",)+r for r in sorted(wd-gd)])

if __name__=="__main__":
	import sys
	properties(sys.stdout)
	qualifiers(sys.stdout)
