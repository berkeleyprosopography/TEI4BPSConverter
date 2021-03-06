# TEI4BPSConverter

This tool converts schema-compliant CSV files in TEI4BPS format. 

## Schema 

The schema, as exemplified in the example corpus, calls for the following fields


| Attribute     | Type          | Example  |
| ------------- |-------------| -----|
| Text_ID       | string		| P.Mich. V 238 I 10 |
| Date		    | date 	        |   12 feb 46 BC |
| Activity      | string      |   Land sale |
| Activity_sequence      | int      |   2 |
| Activity_attribute | taglist |    Object:Land &#124; LandType:Fruit garden |
| Role      | string | Lessor|
| Role_attribute      | taglist | ?|
| Person_name      | string      |   Harmaeis |
| Person_sequence      | int      |   2 |
| Person_attribute | taglist      |    NameType:Greek &#124; Gender:Male |
| Person_relation | taglist      |    Mother:5 &#124; Father:Ano-Uballit |

### Taglists

Taglists are strings in the format

	key : value 

chained together by pipes (|), like so:

	key : value | key : value | key : value 

The key is going to be interpreted as an attribute of the object it refers to. The converter makes no assumption about the meaning of these tags, other than expecting them to be type-compliant.

## Usage

Run with 

    python convert.py -i input_data.csv
    
Optionally, output to file with 

    python convert.py --input input_data.csv --output outfile
    
## Obtaining this code

You will need git and pip installed. 
Open terminal in a parent folder of your choice and do 

	git clone git@github.com:berkeleyprosopography/TEI4BPSConverter.git
	
This will create a local copy of this codebase on your computer. 
Alternatively, you can click on "Download ZIP" on the sidebar and uncompress said zip file in a folder of your choice.

After you have obtained the code, you will need to install the libraries to make the converter run. 
If you do not wish to install the libraries system-wide, you can use a virtual environment, like so

	virtualenv venv
	source venv/bin/activate
	pip install -r requirements.txt
	
Or you can install directly on your system with:
	
	sudo pip install -r requirements.txt
	
