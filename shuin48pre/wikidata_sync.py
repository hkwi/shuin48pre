import rdflib
import csv
import os.path

ns={}
for k,v in csv.reader(open(os.path.join(os.path.dirname(__file__), "ns.csv"))):
	globals()[k.upper()] = rdflib.Namespace(v)
	ns[k] = v

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
	out.writerows([("ours",)+r for r in gd-wd])
	out.writerows([("wikidata",)+r for r in wd-gd])

if __name__=="__main__":
	import sys
	qualifiers(sys.stdout)
