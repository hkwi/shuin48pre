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
		with open("docs/senkyo_dotcom.csv", "w") as fp:
			shuin48pre.senkyo_dotcom.run(fp)
	
	th2 = threading.Thread(target=wrap)
	th2.start()
	
	th.join()
	th2.join()
