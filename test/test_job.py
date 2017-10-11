import threading
import shuin48pre.kyousanto_official
import shuin48pre.senkyo_dotcom
import shuin48pre.ishin_official
import shuin48pre.koumei_official
import shuin48pre.koumei_official_hirei
import shuin48pre.koufuku_official
import shuin48pre.asahi
import shuin48pre.mainichi

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
	
	def wrap5():
		with open("docs/koumei_official.csv", "w") as fp:
			shuin48pre.koumei_official.run(fp)
	th5 = threading.Thread(target=wrap5)
	th5.start()
	
	def wrap6():
		with open("docs/koumei_official_hirei.csv", "w") as fp:
			shuin48pre.koumei_official_hirei.run(fp)
	th6 = threading.Thread(target=wrap6)
	th6.start()
	
	def wrap7():
		with open("docs/koufuku_official.csv", "w") as fp:
			shuin48pre.koufuku_official.run(fp)
	
	th7 = threading.Thread(target=wrap7)
	th7.start()
	
	def wrap8():
		with open("docs/asahi.csv", "w") as fp:
			shuin48pre.asahi.run(fp)
	
	th8 = threading.Thread(target=wrap8)
	th8.start()
	
	def wrap9():
		with open("docs/mainichi.csv", "w") as fp:
			shuin48pre.mainichi.run(fp)
	
	th9 = threading.Thread(target=wrap9)
	th9.start()
	
	th.join()
	th2.join()
	th3.join()
	th4.join()
	th5.join()
	th6.join()
	th7.join()
	th8.join()
	th9.join()
