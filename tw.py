import json
import re
import os
import csv
import logging
import twitter
import time
import rdflib
import urllib.parse
from twitter.oauth import OAuth, read_token_file

def from_gray_db():
	db = csv.reader(open("docs/gdoc_gray_db.csv", encoding="UTF-8"))
	db = [r for r in db if "".join(r)]
	for i, r in enumerate(db):
		if "wikidata" in r:
			break
	for j,n in enumerate(db[i]):
		if "twitter" in n:
			break
	ret = []
	for r in db[i+1:]:
		for v in r[j].split("\n"):
			v = v.strip()
			if not v or v == "-":
				continue
			if re.match("https?://", v):
				pc = urllib.parse.urlparse(v)
				assert "twitter" in pc.netloc
				v = pc.path[1:]
			if v[0] in "@＠":
				v = v[1:]
			ret.append(v)
	return ret

def from_wikidata():
	w = rdflib.ConjunctiveGraph(store="SPARQLStore")
	w.store.endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
	res = w.query('''
	SELECT * WHERE {
		?p wdt:P3602 wd:Q20983100 .
		?p wdt:P2002 ?t .
	}
	''')
	return [r["t"].value for r in res]

twitter_ids = set(from_gray_db() + from_wikidata())

a = json.load(open("twitter_credential.json"))
auth = OAuth(a["auth_token"], a["auth_secret"], a["consumer_key"], a["consumer_secret"])

keys = 'id_str name screen_name location description created_at time_zone lang profile_background_color profile_background_image_url profile_background_image_url_https profile_image_url profile_image_url_https profile_link_color profile_sidebar_border_color profile_sidebar_fill_color profile_text_color translator_type protected verified default_profile has_extended_profile'.split()

out = csv.writer(open("twitter_sn_info.csv","w"))
out.writerow(["asis", "err_data"]+keys)
tw = twitter.Twitter(auth=auth, api_version="1.1", domain="api.twitter.com")
for i,name in enumerate(sorted(twitter_ids)):
	time.sleep(1)
	if not name or name == "-":
		continue
	print("%d/%d %s" % (i, len(twitter_ids), name))
	try:
		r = tw.users.show(screen_name=name)
		out.writerow([name, "-"]+[r[k] for k in keys])
	except twitter.api.TwitterHTTPError as e:
		out.writerow([name, json.dumps(e.response_data)]+["-"]*len(keys))
	except Exception as e:
		logging.error(type(e))
		logging.error(e)
		continue

import json
import csv
keys = "asis error screen_name verified default_profile has_extended_profile".split()
out = csv.writer(open("docs/twitter_sn_map.csv","w"))
out.writerow(keys)
for r in csv.DictReader(open("twitter_sn_info.csv")):
	r["error"]=""
	try:
		r["error"] = json.loads(r["err_data"])["errors"][0]["message"]
	except:
		pass
	out.writerow([r[k] for k in keys])
