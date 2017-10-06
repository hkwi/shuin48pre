import threading
import shuin48pre.kyousanto_official
import shuin48pre.senkyo_dotcom

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
	
	th.join()
	th2.join()
	th3.join()
