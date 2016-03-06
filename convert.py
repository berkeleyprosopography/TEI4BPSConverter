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
from datautil.date import parse


# Configure argparser
parser = argparse.ArgumentParser( description='Convert CSV to TEI')
parser.add_argument('--output', '-o', default=None, type=str,
                    help="relative path of output file")
parser.add_argument('--input', '-i', default=None, type=str,
                    help="relative path of input file")
parser.add_argument('--params', '-p', default=None, type=str,
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
    Date     			= 1
    Activity            = 2
    Activity_sequence	= 3
    Activity_attribute  = 4
    Role             	= 5
    Role_attribute      = 6
    Person_name         = 7
    Person_sequence		= 8
    Person_attribute    = 9
    Person_relation		= 10


def parse_date(input_date):
	ret = ""
	try:
		ret = parse(unicode(input_date, "utf-8"))
	except Exception as e:
		log.error('Could not process date "{0}", skipping.'.format(input_date))
		log.error('Error is: {0}'.format(str(e)))
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


def get_header(anchor): 
	header = etree.SubElement(anchor, "teiHeader")
	fdesc = etree.SubElement(header, "fileDesc")
	title = etree.SubElement(fdesc, "titleStmt")
	pub = etree.SubElement(fdesc, "publicationStmt")
	sdesc = etree.SubElement(fdesc, "sourceDesc")
	p_sdesc = etree.SubElement(sdesc, "p")

def ingest(file, params):
	log.warn("Loading {0}".format(str(file)))
	f = open(file, 'rU')
	print params
	if params=="excel":
		c = csv.reader(f, dialect=csv.excel_tab)
	else:
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
	get_header(root)

	# This loop iterates over the documents in the Defaultdict
	for document in data:
		# Header goes here

		tei = etree.SubElement(root, 'TEI')
		get_header(tei)

		text = etree.SubElement(tei, "text")
		text.attrib["text_ID"] = str(document)


		# Find all activities inside a document
		activities = defaultdict(list)
		for line in data[document]:
			date = parse_date(line[Field.Date])
			try:
				activities[str(date)].append(line)
			except Exception as e:
				log.error('Not going to add "{0}" to {1}.'.format(date, document))
				log.error('Error is: {0}'.format(str(e)))

		log.warn("Found {0} activities in document {1}, ".format( len(activities), str(line[Field.Text_ID])))

		# Traverse the activities list
		for uid, activity in enumerate(activities):

			data_entry = activities[activity][uid]
		
			body = etree.SubElement(text, "body")

			div = etree.SubElement(body, "div" )
			div.attrib["type"] = "activity"
			div.attrib["subtype"] = str(data_entry[Field.Activity])
			div.attrib["full_date"] = activity

			# Add attributes
			for key, value in parse_tags(str(data_entry[Field.Activity_attribute])).iteritems():
				tag = etree.SubElement(div, "state" )
				tag.attrib["type"] = str(key)
				tag.text = str(value)

			# Add persons
			perslist = etree.SubElement(div, 'p')
			perslist.attrib["type"] = "persons_list"

			for person in activities[activity]:
				pers_name = etree.SubElement(perslist, "persName")
				pers_name.attrib['role'] = str(person[Field.Role])
				pers_name.attrib['uid'] = str(person[Field.Person_sequence])

				if person[Field.Person_name]:
					pers_forename = etree.SubElement(pers_name, "forename")
					pers_forename.text = clean_ascii(person[Field.Person_name])

				for key, value in parse_tags(str(person[Field.Person_attribute])).iteritems():
					tag = etree.SubElement(pers_name, "state" )
					tag.attrib["type"] = str(key)
					tag.text = str(value)

				# This is the content of the "relation" feature
				if person[Field.Person_relation]:
					for key, value in parse_tags(str(person[Field.Person_relation])).iteritems():
						tag = etree.SubElement(pers_name, "state" )
						tag.attrib["type"] = str(key)
						tag.text = str(value)



	log.warn("Ok, conversion complete.")
	return etree.tostring(root, pretty_print=True)
	

if __name__ == "__main__": 
	log.info("Welcome to CSV to TEI4BPS conversion tool.")
	data, size, input_file = ingest(args.input, args.params)
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


