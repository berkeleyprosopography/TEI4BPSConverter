#!/bin/python

'''
CSV to TEI4BPS converter

Written by Davide Semenzin
Berkeley Prosopography Services				

'''

import os, csv
from lxml import etree
import argparse
from curses import ascii
from collections import defaultdict
from colorlog import ColoredFormatter
import logging
import time
from enum import Enum
from dateutil.parser import parse


# Configure argparser
parser = argparse.ArgumentParser( description='Convert CSV to TEI')
parser.add_argument('--output', '-o', default=None, type=str,
                    help="relative path of output file")
parser.add_argument('--input', '-i', default=None, type=str,
                    help="relative path of input file")
args = parser.parse_args()

# Configure logging
LOG_LEVEL = logging.DEBUG
LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger('TEI4BPS Converter')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

# Define the attribute mapping to CSV columns
class Field(Enum):
    Text_ID           	= 0
    Date     			= 4
    Activity            = 5
    Activity_attribute  = 6
    Role             	= 7
    Role_attribute      = 8
    Person_name         = 9
    Person_attribute    = 10
    Relation			= 11


def parse_date(input_date):
	ret = ""
	try:
		ret = parse(input_date)
	except:
		log.error('Could not process date "{0}", skipping.'.format(input_date))
	return ret

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
	log.warn("Loading {0}".format(str(file)))
	f = open(file, 'r')
	c = csv.reader(f)
	data = defaultdict(list)

	size =0
	for line in c:
		data[str(line[0])].append(line)
		size += 1

	log.warn("Found {0} documents basing on Text_ID".format(len(data)))
	return data, size, f


def convert(data, size):	
	log.warn("Now converting {0} rows in {1} documents to TEI4BPS. (Average of {2} rows per document)".format( size, len(data), size/len(data) ))
	root = etree.Element('teiCorpus')

	# This loop iterates over the documents in the Defaultdict
	for document in data:
		# Header goes here

		tei = etree.SubElement(root, 'TEI')
		text = etree.SubElement(tei, "text")
		text.attrib["text_ID"] = str(document)


		# Find all activities inside a document
		activities = defaultdict()
		for line in data[document]:
			date = str(parse_date(line[Field.Date]))
			try:
				activities[date].append(line)
			except:
				log.error('Not going to add "{0}".'.format(date))

		# Find all persons inside an activity
		for activity in activities:
			log.warn("Processing document {0}, ".format(str(line[Field.Text_ID])))


			text.attrib["full_date"] = str(parse_date(line[Field.Date]))
			#day, month, year = line[1], line[2], line[3]
			#text.attrib["full_date"] = str(day + ' ' + month + ' ' + year + "AD")
			
			body = etree.SubElement(text, "body")

			div = etree.SubElement(body, "div" )
			div.attrib["type"] = "activity"
			div.attrib["subtype"] = str(line[Field.Role])
			
			for key, value in parse_tags(str(line[Field.Role_attribute])).iteritems():
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

	log.warn("Ok, conversion complete.")
	return etree.tostring(root, pretty_print=True)
	

if __name__ == "__main__": 
	log.info("Welcome to CSV to TEI4BPS conversion tool.")
	data, size, input_file = ingest(args.input)
	start = time.time()
	s = convert(data, size)
	end = time.time()

	if args.output:
		log.info("Writing to {0}".format(args.output))
		with open(args.output, "w+") as text_file:
		    text_file.write(s)
	else:
		print s

	log.info("Conversion took {0} seconds.".format(end-start))
	log.info("Bye!")


