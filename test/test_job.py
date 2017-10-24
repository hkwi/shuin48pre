import threading
import shuin48pre.kyousanto_official
import shuin48pre.senkyo_dotcom
import shuin48pre.ishin_official
import shuin48pre.koumei_official
import shuin48pre.koumei_official_hirei
import shuin48pre.koufuku_official
import shuin48pre.asahi
import shuin48pre.mainichi
import shuin48pre.jimin_official
import shuin48pre.kibou_official
import shuin48pre.gdoc
import shuin48pre.wikidata_sync
import shuin48pre.wikidata47_sync

def spawn(prog, file, *args):
	def wrap():
		with open(file, "w") as fp:
			prog(fp, *args)
	return threading.Thread(target=wrap)

def test_jobs():
	jobs = [
		(shuin48pre.kyousanto_official.run, "docs/kyousanto_official.csv"),
		(shuin48pre.senkyo_dotcom.run, "docs/senkyo_dotcom_hirei.csv", True),
		(shuin48pre.senkyo_dotcom.run, "docs/senkyo_dotcom.csv", False),
#		(shuin48pre.ishin_official.run, "docs/ishin_official.csv"),
		(shuin48pre.koumei_official.run, "docs/koumei_official.csv"),
		(shuin48pre.koumei_official_hirei.run, "docs/koumei_official_hirei.csv"),
		(shuin48pre.koufuku_official.run, "docs/koufuku_official.csv"),
		(shuin48pre.jimin_official.run, "docs/jimin_official.csv"),
		(shuin48pre.asahi.run, "docs/asahi.csv"),
		(shuin48pre.mainichi.run, "docs/mainichi.csv"),
		(shuin48pre.jimin_official.run, "docs/jimin_official.csv"),
#		(shuin48pre.kibou_official.run, "docs/kibou_official.yaml"),
	]
	
	ths = [spawn(*j) for j in jobs]
	[th.start() for th in ths]
	[th.join() for th in ths]

def test_gdoc():
	with open("docs/database.csv", "w", encoding="utf-8-sig") as fp:
		shuin48pre.gdoc.run(fp)

def test_wikidata():
	shuin48pre.wikidata_sync.qualifiers(open("docs/wikidata_P3602_Q20983100.csv","w"))
	shuin48pre.wikidata_sync.properties(open("docs/wikidata_properties.csv","w"))
	shuin48pre.wikidata47_sync.term(open("docs/wikidata_term_for_47ge.csv","w"))
	shuin48pre.wikidata47_sync.general_election(open("docs/wikidata_P3602_Q4638550.csv","w"))
