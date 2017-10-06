import threading
import shuin48pre.kyousanto_official
import shuin48pre.senkyo_dotcom
import shuin48pre.ishin_official

def test_jobs():
	def wrap():
		with open("docs/kyousanto_official.csv","w") as fp:
			shuin48pre.kyousanto_official.run(fp)
	th = threading.Thread(target=wrap)
	th.start()
	
	def wrap2():
		with open("docs/senkyo_dotcom_hirei.csv", "w") as fp:
			shuin48pre.senkyo_dotcom.run(fp, True)
	th2 = threading.Thread(target=wrap2)
	th2.start()
	
	def wrap3():
		with open("docs/senkyo_dotcom.csv", "w") as fp:
			shuin48pre.senkyo_dotcom.run(fp, False)
	th3 = threading.Thread(target=wrap3)
	th3.start()
	
	def wrap4():
		with open("docs/ishin_official.csv", "w") as fp:
			shuin48pre.ishin_official.run(fp)
	th4 = threading.Thread(target=wrap4)
	th4.start()
	
	th.join()
	th2.join()
	th3.join()
	th4.join()
