import re
import os
import csv
import rdflib
import yaml

ns={}
for k,v in csv.reader(open(os.path.join(os.path.dirname(__file__), "ns.csv"))):
	globals()[k.upper()] = rdflib.Namespace(v)
	ns[k] = v

def yaml_lut(filename):
	lut = {}
	for k,vs in yaml.load(open(filename)).items():
		for v in vs:
			lut[v] = k
	return lut

def general_election(fp):
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
	  ?person p:P3602 ?st .
	  ?st ps:P3602 wd:Q4638550 .
	  OPTIONAL { ?st pq:P768 ?area . }
	  OPTIONAL { ?st pq:P1268 ?party . }
	  OPTIONAL { ?st pq:P1111 ?votes . }
	}
	''')
	wd = []
	for r in res:
		s = [r["person"], "", "", ""]
		
		if r["area"]:
			s[1] = r["area"][len(WD):]
		if r["party"]:
			s[2] = r["party"][len(WD):]
		if r["votes"]:
			s[3] = r["votes"].value
	
	gd = []
	areas = yaml_lut("docs/area.yml")
	for t in csv.DictReader(open("docs/shuin47post.csv")):
		if t["wikidata"] in ("","-"):
			continue
		qname = t["wikidata"]
		single = t["47回衆議院総選挙 小選挙区 結果"]
		if single != "-":
			gd.append((qname, areas[single], "", ""))
		hirei = t["47回衆議院総選挙 比例区 結果"]
		if hirei != "-":
			gd.append((qname, areas[hirei], "", ""))
	
	out = csv.writer(fp)
	out.writerow("db person area party votes".split())
	out.writerows([("codefor",)+r for r in sorted(set(gd)-set(wd))])
	out.writerows([("wikidata",)+r for r in sorted(set(wd)-set(gd))])

def term(fp):
	party_lut = yaml_lut("docs/party.yml")
	
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
	  ?person p:P39 ?st .
	  ?st ps:P39 wd:Q17506823 ;
	      pq:P2937 wd:Q41654707 .
	  OPTIONAL { ?st pq:P4100 ?party . }
	}
	''')
	wd = []
	for r in res:
		if r["party"]:
			wd.append((r["person"][len(WD):], r["party"][len(WD):]))
		else:
			wd.append((r["person"][len(WD):], ""))
	
	gd = []
	for t in csv.DictReader(open("docs/shuin47post.csv")):
		if t["wikidata"] in ("","-"):
			continue
		gd.append((t["wikidata"], party_lut[t["party_ref"]]))
	
	out = csv.writer(fp)
	out.writerow(("db","qname","party"))
	for t in sorted(set(wd)-set(gd)):
		out.writerow(["wikidata"]+list(t))
	for t in sorted(set(gd)-set(wd)):
		out.writerow(["codefor"]+list(t))

if __name__ == "__main__":
	import sys
	term(sys.stdout)
	general_election(sys.stdout)
