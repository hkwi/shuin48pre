import re
import os
import csv
import rdflib

ns={}
for k,v in csv.reader(open(os.path.join(os.path.dirname(__file__), "ns.csv"))):
	globals()[k.upper()] = rdflib.Namespace(v)
	ns[k] = v

def general_election(fp):
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
	  ?person p:P3602 ?st .
	  ?st ps:P3602 wd:Q4638550 .
	  OPTIONAL { ?st pq:P768 ?area . }
	}
	''')
	wd = []
	for r in res:
		if r["area"]:
			wd.append((r["person"][len(WD):], r["area"][len(WD):]))
		else:
			wd.append((r["person"][len(WD):], ""))
	
	gd = []
	areas = dict(csv.reader(open("docs/areas.csv")))
	for t in csv.DictReader(open("docs/shuin47post.csv")):
		if t["wikidata"] in ("","-"):
			continue
		qname = t["wikidata"]
		single = t["47回衆議院総選挙 小選挙区 結果"]
		if single != "-":
			k = "%s第%s" % re.match("(.*?)(\d+区)", single).groups()
			gd.append((qname, areas[k]))
		hirei = t["47回衆議院総選挙 比例区 結果"]
		if hirei != "-":
			gd.append((qname, areas["比例%sブロック" % hirei]))
	
	out = csv.writer(fp)
	out.writerow(("db","qname","area"))
	for t in sorted(set(wd)-set(gd)):
		out.writerow(["wikidata"]+list(t))
	for t in sorted(set(gd)-set(wd)):
		out.writerow(["codefor"]+list(t))

def term(fp):
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
	  ?person p:P39 ?st .
	  ?st ps:P39 wd:Q17506823 ;
	      pq:P2937 wd:Q41654707 .
	}
	''')
	wd = [r["person"][len(WD):] for r in res]
	gd = [t["wikidata"] for t in csv.DictReader(open("docs/shuin47post.csv")) if t["wikidata"] not in ("","-")]
	
	out = csv.writer(fp)
	out.writerow(("db","qname"))
	for t in sorted(set(wd)-set(gd)):
		out.writerow(["wikidata",t])
	for t in sorted(set(gd)-set(wd)):
		out.writerow(["codefor",t])

if __name__ == "__main__":
	import sys
#	term(sys.stdout)
	general_election(sys.stdout)
