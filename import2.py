#!/bin/python

'''
This scripts folllows this attribute mapping

0	text_ID
1	Day
2	Month
3	Year
4	Activity
5	Activity_attribute
6	Role
7	Person_name
8	Person_attribute					

'''

import os, csv
from lxml import etree
import argparse
from curses import ascii
from collections import defaultdict

parser = argparse.ArgumentParser( description='Convert CSV to TEI')

parser.add_argument('--output', '-o', default=None, type=str,
                    help="relative path of output file")

parser.add_argument('--input', '-i', default=None, type=str,
                    help="relative path of input file")

args = parser.parse_args()


def parse_tags(input_string):
	ret = {}
	try: 
		pairs = input_string.split('|')
		for pair in pairs:
			a = pair.split(':')
			ret[a[0].strip()] = a[1].strip()
	except:
		pass
	return ret

def clean_ascii(text):
    return str(''.join(
            ascii.isprint(c) and c or '?' for c in text
            )) 

def ingest(file):
	f = open(file, 'r')
	c = csv.reader(f)
	ret = defaultdict(list)

	for line in c:
		ret[str(line[0])].append(line)

	print "Read {0} documents".format(len(ret))

	return ret


def convert(data):	

	root = etree.Element('teiCorpus')

	for document in data:

		tei = etree.SubElement(root, 'TEI')
		text = etree.SubElement(tei, "text")
		text.attrib["text_ID"] = str(document)

		for line in data[document]:
			print "line", line

			day, month, year = line[1], line[2], line[3]
			
			text.attrib["full_date"] = str(day + ' ' + month + ' ' + year + "AD")
			
			body = etree.SubElement(text, "body")

			div = etree.SubElement(body, "div" )
			div.attrib["type"] = "activity"
			div.attrib["subtype"] = str(line[4])
			
			for key, value in parse_tags(str(line[5])).iteritems():
				tag = etree.SubElement(div, "feature" )
				tag.attrib[str(key)] = str(value)

			perslist = etree.SubElement(div, 'p')

			pers1name = etree.SubElement(perslist, "persName")
			pers1name.attrib['role'] = str(line[6])

			pers_forename = etree.SubElement(pers1name, "forename")
			pers_forename.text = clean_ascii(line[7])

			for key, value in parse_tags(str(line[5])).iteritems():
				tag = etree.SubElement(div, "feature" )
				tag.attrib[str(key)] = str(value)


	return etree.tostring(root, pretty_print=True)
	

if __name__ == "__main__": 
	data = ingest(args.input)
	s = convert(data)

	if args.output:
		s.write(args.output)
	else:
		print s


