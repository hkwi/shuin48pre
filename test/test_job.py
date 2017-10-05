import threading
import shuin48pre.kyousanto_official

def test_jobs():
	def wrap():
		with open("docs/kyousanto_official.csv","w") as fp:
			shuin48pre.kyousanto_official.run(fp)
	
	th = threading.Thread(target=wrap)
	th.start()
	th.join()
