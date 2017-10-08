import csv
import sys
import re
import xlrd
import unicodedata

def is_kana(s):
	for ss in s:
		n = unicodedata.name(ss)
		if n.startswith("HIRAGANA") or n.startswith("KATAKANA"):
			continue
		return False
	return True

def dels(s):
	return re.sub("[　 ]+", "", s)

def proc(out, filename, push):
	book = xlrd.open_workbook(filename)
	for sheet_n, sheet in enumerate(book.sheets()):
		index_row = None
		for row_n, row in enumerate(sheet.get_rows()):
			rowtxt = "".join([c.value.strip() for c in row if isinstance(c.value, str)])
			rowtxt = re.sub("[　 ]+", "", rowtxt)
			if "候補者" in rowtxt:
				index_row = row_n
		
		end_row = None
		for row_n, row in enumerate(sheet.get_rows()):
			if row_n <= index_row:
				continue
			rowtxt = re.sub("[　 ]+", "", "".join([str(c.value) for c in row]))
			if not rowtxt:
				break
			if rowtxt.startswith("※"):
				break
			end_row = row_n
		
		name_range = []
		for i, cell in enumerate(sheet.row(index_row)):
			if isinstance(cell.value, str):
				if "候" in cell.value:
					name_range.append(i)
				if "生年月日" == re.sub("[　 ]+", "", cell.value):
					name_range.append(i)
		
		assert len(name_range) == 2
		
		for row_n, row in enumerate(sheet.get_rows()):
			if row_n <= index_row:
				continue
			if row_n > end_row:
				break
			
			if not "".join([str(r) for r in row]):
				break
			
			area = ""
			for i,c in enumerate(row):
				if i < name_range[0]:
					if isinstance(c.value, float):
						area += str(int(c.value))
					else:
						area += str(c.value)
			if re.search("\d$", area):
				area += "区"
			
			yomi_names = []
			for i,c in enumerate(row):
				if i < name_range[0]:
					continue
				if i >= name_range[1]:
					break
				if not isinstance(c.value, str) or not c.value:
					continue
				
				yomi_name = c.value.split("\n")
				if len(yomi_name)==1 and dels(yomi_name[0])=="ふくしろう":
					yomi_name += ["福志郎"]
				if len(yomi_name)==1 and is_kana(dels(yomi_name[0])):
					yomi_name *= 2
				assert len(yomi_name)==2, (yomi_name, sheet_n, row_n)
				yomi_names += [yomi_name]
			if len(yomi_names)==2:
				sei_hira = dels(yomi_names[0][0])
				mei_hira = dels(yomi_names[1][0])
				sei = dels(yomi_names[0][1])
				mei = dels(yomi_names[1][1])
			elif len(yomi_names)==1:
				ns1 = re.split("[　 ]+", yomi_names[0][0], 1)
				ns2 = re.split("[　 ]+", yomi_names[0][1], 1)
				if len(ns1)==2 and len(ns2)==2:
					sei_hira = dels(ns1[0])
					mei_hira = dels(ns1[1])
					sei = dels(ns2[0])
					mei = dels(ns2[1])
				elif len(ns1)==1 and len(ns2)==2:
					if is_kana(ns2[0]):
						sei_hira = dels(ns2[0])
						mei_hira = dels(ns1[0])
						sei = dels(ns2[0])
						mei = dels(ns2[1])
					elif is_kana(ns2[1]):
						sei_hira = dels(ns1[0])
						mei_hira = dels(ns2[1])
						sei = dels(ns2[0])
						mei = dels(ns2[1])
					else:
						assert False, (ns1, ns2)
				else:
					assert False, (ns1, ns2)
			else:
				assert False, row
			
			birth = None
			age = None
			gender = None
			prev = None
			bio = None
			for i,c in enumerate(row):
				if i < name_range[1]:
					continue
				if isinstance(c.value, str):
					m1 = re.match("(昭和|平成)(\d+)年(\d+)月(\d+)日", c.value)
					if m1:
						bd = m1.groups()
						if bd[0] == "昭和":
							birth = "%d-%02d-%02d" % (1925+int(bd[1]), int(bd[2]), int(bd[3]))
						continue
					
					if dels(c.value) in "男女":
						gender = dels(c.value)
						continue
					
					if gender is None:
						prev = dels(c.value)
					elif bio is None:
						bio = c.value
				elif isinstance(c.value, (int, float)):
					age = int(c.value)
			assert birth
			
			hirei = None
			if not area.endswith("区"):
				hirei = area
				area = None
			
			out.writerow((area, hirei, sei, mei, sei_hira, mei_hira, gender, birth, prev, bio))


if __name__=="__main__":
	out = csv.writer(open("docs/jimin_official.csv", "w"))
	proc(out, "docs/135811_1.xlsx", "公認")
	proc(out, "docs/135811_2.xlsx", "推薦予定")
	proc(out, "docs/135811_3.xlsx", "推薦")
