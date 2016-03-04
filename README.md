# TEI4BPSConverter

This tool converts schema-compliant CSV files in TEI4BPS format. 

## Schema 

The schema, as exemplified in the example corpus, calls for the following fields


| Attribute     | Type          | Example  |
| ------------- |-------------| -----|
| Text_ID       | string		| P.Mich. V 238 I 10 |
| Day		    | int 	        |   12 |
| Month 		| int      		|    1 |
| Year	        | int 			| 44 |
| Activity      | string      |   Land sale |
| Activity_attribute | taglist |    Object:Land &#124; LandType:Fruit garden |
| Role      | string | Lessor|
| Person_name      | string      |   Harmaeis |
| Person_attribute | taglist      |    NameType:Greek &#124; Gender:Male |
			

### Taglists

Taglists are strings in the format

	key : value 

chained together by pipes (|), like so:

	key : value | key : value | key : value 

The key is going to be interpreted as an attribute of the object it refers to. The converter makes no assumption about the meaning of these tags, other than expecting them to be type-compliant.

## Usage

Run with 

    python TEI-import.py --input input_data.csv
    
Optionally, output to file with 

    python TEI-import.py --input input_data.csv --output outfile