#!/bin/python

'''
CSV to TEI4BPS converter

Written by Davide Semenzin
Berkeley Prosopography Services             

'''

import sys, os, csv
from lxml import etree
import argparse
from curses import ascii
from collections import defaultdict
#from colorlog import ColoredFormatter
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
#LOGFORMAT = "  %(levelname)-8s%(reset)s | %(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
#formatter = logging.Formatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
#stream.setFormatter(formatter)
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


def get_header(anchor, text_id = None): 
    header = etree.SubElement(anchor, "teiHeader")
    fdesc = etree.SubElement(header, "fileDesc")
    title = etree.SubElement(fdesc, "titleStmt")
    if text_id:
        title_node = etree.SubElement(title, "title")
        name_node = etree.SubElement(title_node, "name")
        name_node.attrib['type'] = "cdlicat:id_text"
        name_node.text = text_id

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
        log.error("Loaded document {0}: {1} entries".format(str(document), len(data[document])))
        tei = etree.SubElement(root, 'TEI')
        get_header(tei, document)

        text = etree.SubElement(tei, "text")
        text.attrib["text_ID"] = str(document)
        text.attrib["type"] = 'transliteration'

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

        # Traverse the activities list (binned by date, one activity is a sub-list of the main table)
        # (This will become important once we allow multiple activities in a document)
        for uid, activity in enumerate(activities):
            print activities[activity], uid

        for uid, activity in enumerate(activities):
            print uid
            print activity
            print "* Processing activity {0}/{1} in document {2}".format(uid,len(activities), activity)
            data_entry = activities[activity][uid]
            #data_entry = activity
            #print 'LOOPING OVER ACTIVITY', uid,len(activities), activity, 
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
                
            # Here we iterate on every line of the activity 
            for linenum, line in enumerate(act):
                #print "\n"
                print "## Processing line {0} out of {1} *".format(linenum +1, len(act))
                print "## --->", linenum, line, '|', uid, activity
                
                # a convenient try-catch that makes debug easier. 
                try:
                    # First of all we check that we have a person with a role 
                    # and if so, we go ahead and create a node for it
                    if line[Field.Role]:
                        print "### Found person {0} in role {1}".format(line[Field.Person_name] , line[Field.Role])
                        pers_name = etree.Element( "persName")
                        pers_name.attrib['role'] = str(line[Field.Role])
                        pers_name.attrib['uid'] = str(line[Field.Person_sequence])

                        if line[Field.Person_sequence]:
                            pers_forename = etree.SubElement(pers_name, "forename")
                            pers_forename.text = clean_ascii(line[Field.Person_name])
                            
                            for tag in parse_tags(line[Field.Person_attribute]).items():
                                elem = etree.SubElement(pers_forename, "state" )
                                elem.attrib["type"] = str(tag[0])
                                elem.text = str(tag[1])

                            pers_name.append(pers_forename)
                            perslist.append(pers_name)
                            print "### OK Added new ", etree.tostring(pers_name)

                            processed_relations =[]
                            
                            if line[10]:
                                tags = parse_tags(line[10])
                                print "$$$ Resolving forenames in person_relation", tags
                                
                                for tag in tags.items():
                                    # resolve person name
                                    person = persons_by_sequence[int(tag[1])]
                                    print "$$$ Iterating over tag", tag,' ->', person[7]

                                    print "$$$ is {0} a patronymic?".format(tag[0]), tag[0].lower() == "son"
                                    # check whether it's a patronymic
                                    if tag[0].lower() == "son":
                                        print "$$$ let's add it to the tree"
                                        pf = etree.Element("forename")
                                        pf.text = clean_ascii(person[Field.Person_name])
                                        pf.attrib['type'] = "patronymic"
                                        
                                        for ptag in parse_tags(line[Field.Person_attribute]).items():
                                            elem = etree.SubElement(pf, "state" )
                                            elem.attrib["type"] = str(ptag[0])
                                            elem.text = str(ptag[1])
                                        #print " (A patronymic is its own forename)"
                                        print "$$$$  [DEBUG] Now pers_name looks like", etree.tostring(pers_name)
                                        pers_name.append(pf)
                                        print "$$$$  CHECKPOINT -> Added", etree.tostring(pf)
                                        print "$$$$  [DEBUG] Now pers_name looks like", etree.tostring(pers_name)

                                    else:
                                        pf = etree.Element("state")
                                        pf.attrib["type"] = str(tag[0])
                                        pf.text = str(tag[1])
                                        print "$$$$  [DEBUG] Now pers_forename looks like", etree.tostring(pers_forename)
                                        pers_forename.append(pf)
                                        print "$$$$ CHECKPOINT -> Added", etree.tostring(pf)
                                        print "$$$$ [DEBUG] Now pers_forename looks like", etree.tostring(pers_forename)

                                    print "$$$ Processed all record information for", person[7]

                                    processed_relations.append(person[8])
                            else:
                                print "$$$ Person_relation not found, skipping..."
                            
                            print "### CHECKPOINT -> Now LOOKAHEAD to find unbound fliation information"
                        
                        
                        loop = True
                        i = 1
                        bucket_list = []
                        # construct bucket list
                        while loop is True and ((i + linenum) < len(act)):
                            print "=== Lookahead config: loop {0}, linenum {1}, i {2}, i+linenum {3}, len(act)={4}".format(loop, linenum, i, i + linenum, len(act))
                            tags = parse_tags(act[linenum + i][10])
                            for tag in tags:
                                tags[tag] = persons_by_sequence[int(tags[tag])][7]
                            print "=== Looking ahead {0} items. Found {1} ({2})".format(i, act[linenum + i][7], tags)
                            if act[linenum + i][5] != '':
                                print "=== stop at", act[linenum + i][7], act[linenum + i][10]
                                loop = False
                            else:
                                print "=== It appears {0} ({1}) is part of this context.".format(act[linenum + i][7], act[linenum + i][10] or 'NO RELATION')
                                bucket_list.append(act[linenum + i])
                            i +=1

                        # process bucket list
                        print "BUCKET LIST LENGTH:", len(bucket_list)
                        for person in bucket_list:
                            print "--- Sorting item {0} in bucket list".format(person)
                            print "--- Does it have a name?"
                            if person[7]:
                                print "---  Yes, {0} looks like a person name. Did we already process it?".format(person[7])
                                if person[8] not in processed_relations:
                                    print '---  No! We have an UNBOUND item:', person[9], person[7]
                                    # let's add it

                                    if person[9].lower()=='clan':
                                        print '---   It is a CLAN!', person[7]
                                        # adding clan
                                        pf = etree.Element("addName")
                                        pf.text = clean_ascii(person[Field.Person_name])
                                        pf.attrib['type'] = "clan"

                                        print "--- [DEBUG] Now pers_name looks like", etree.tostring(pers_name)
                                        pers_name.append(pf)
                                        print "--- CHECKPOINT -> Added", etree.tostring(pf)
                                        print "--- [DEBUG] Now pers_forename looks like", etree.tostring(pers_name)
                                    else:
                                        print "--- [ERROR] Didn't recognize that tag"
                                        print "--- Ask davide to add it to the supported tag list"

                                else:
                                    print "------   Yes we have. Moving on..."

                    else:
                        print "## WARNING: Person {0} does not have a role (got '{1}' instead) and will be skipped.".format(line[7],line[5], )
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print " ************ EXCEPTION, YOUR HONOR!:", str(e), exc_tb.tb_lineno, exc_type
                    pass


    log.warn("Ok, conversion complete!")
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


