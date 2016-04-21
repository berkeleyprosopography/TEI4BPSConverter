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
    Text_ID             = 0
    Date                = 1
    Activity            = 2
    Activity_sequence   = 3
    Activity_attribute  = 4
    Role                = 5
    Role_attribute      = 6
    Person_name         = 7
    Person_sequence     = 8
    Person_attribute    = 9
    Person_relation     = 10



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
    log.warn("Loading {0} with {1} parameters {2}".format(str(file), len(params), params ))
    f = open(file, 'rU')
    
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
        log.error("Loaded document: {0}".format(str(document)))
        tei = etree.SubElement(root, 'TEI')
        get_header(tei)

        text = etree.SubElement(tei, "text")
        text.attrib["text_ID"] = str(document)


        # Find all activities inside a document
        activities = defaultdict(list)
        for line in data[document]:
            log.error("Loaded line: {0}".format(str(line)))
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
            print 'Processing person', data_entry[7]
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

            #for activity in activities:
            # this is the sub-table filtered by "activity"
            act = activities[activity]
            # this is a person-id lookup dict, will be useful later
            persons_by_sequence = dict((int(x[8]), x) for x in act if x[8])
                
            # Here we iterate on every line of the activity (= Person)
            for linenum, line in enumerate(act):
                # a convenient try-catch that makes debug easier. 
                try:
                    # First of all we check that we have a person with a role 
                    if line[Field.Role]:
                        pers_name = etree.Element( "persName")
                        pers_name.attrib['role'] = str(line[Field.Role])
                        pers_name.attrib['uid'] = str(line[Field.Person_sequence])
                    # Otherwise, we just move on
                    else:
                        print "BREAK -> PASSING ON", line
                        pass
                    
                    if line[Field.Person_sequence]:
                        pers_forename = etree.SubElement(pers_name, "forename")
                        pers_forename.text = clean_ascii(line[Field.Person_name])
                        
                        for tag in parse_tags(line[Field.Person_attribute]).items():
                            elem = etree.SubElement(pers_forename, "state" )
                            elem.attrib["type"] = str(tag[0])
                            elem.text = str(tag[1])

                        print "====++++++++++++++========== adding pname ======"
                        pers_name.append(pers_forename)
                        perslist.append(pers_name)
                        print "Added", etree.tostring(pers_name)

                        processed_relations =[]

                        
                        # Then resolving forenames in person_relation, if any
                        if line[10]:
                            tags = parse_tags(line[10])
                            #print "CHECKPOINT -> resolving tags:", tags
                            
                            for tag in tags.items():
                                print "iterating over tag", tag
                                # resolve person name
                                person = persons_by_sequence[int(tag[1])]
                                # check if it's a patronymic
                                if tag[0].lower() == "son":
                                    pf = etree.SubElement(pers_name, "forename")
                                    pf.text = clean_ascii(line[Field.Person_name])
                                    
                                    for tag in parse_tags(line[Field.Person_attribute]).items():
                                        elem = etree.SubElement(pf, "state" )
                                        elem.attrib["type"] = str(tag[0])
                                        elem.text = str(tag[1])

                                    pers_name.append(pf)
                                    print "CHECKPOINT -> patronym found", tag[0], person[7]

                                else:
                                    #print "CHECKPOINT -> Found", tag[0], person[7]
                                    print '                         <forename type="{0}">{1}'.format( tag[0], person[7],)
                                    for tag in parse_tags(person[9]).items():
                                    # first resolving attributes
                                        print '                           <state type="{0}">{1}</state>'.format(tag[0], tag[1])
                                    print '                         </forename>'

                                print "=========== tag ==================== adding pname ======"

                                processed_relations.append(person[8])
                        else:
                            print "Person_relation not found, skipping..."
                        
                        print "CHECKPOINT -> LOOKAHEAD to find unbound fliation information"
                        loop = True
                        i = 0
                        bucket_list = []
                        
                        while loop:
                            i +=1
                            tags = parse_tags(act[linenum + i][10])
                            for tag in tags:
                                tags[tag] = persons_by_sequence[int(tags[tag])][7]
                            print "looking ahead {0} items. Found {1} ({2})".format(i, act[linenum + i][7], tags)
                            if act[linenum + i][5] != '':
                                print "stop at", act[linenum + i][7], act[linenum + i][10]
                                loop = False
                            else:
                                print "hit at", act[linenum + i][7], act[linenum + i][10]
                                bucket_list.append(act[linenum + i])
                        
                        print "bucket list", [x for x in bucket_list]
                            
                            
                        for person in bucket_list:
                            if person[7]:
                                if person[8] not in processed_relations:
                                    print '+++++++++UNBOUND', person
                        
                        
                            
                                

                            
                    else:
                        
                        print "not person at", line[9]
                except Exception as e:
                    print " ************ EXCEPT", str(e)
                    pass


                '''
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
                '''


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


