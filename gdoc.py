import gspread
import oauth2client.service_account
import csv

# download gdoc_credential.json from your google dev console
cr = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(
	"gdoc_credential.json", ['https://spreadsheets.google.com/feeds'])
gs = gspread.authorize(cr)

targets = {
	"gdoc_gray_db.csv":"182l2CexnCqZ0GPSg9sp2XMMfvUC4muuvYFdJp2Q-vkI",
	"gdoc_seiji_navi.csv":"1T6BhIk_TU9KAOmBou8buvMkj_yK4c72jcJMGMOFUAg0",
}
for fn,sh in targets.items():
	s = gs.open_by_key(sh)
	csv.writer(open("docs/%s" % fn, "w")).writerows(s.sheet1.get_all_values())
