#!/usr/bin/python
#coding=utf-8

#TODO: TILDA

import pdftotext
import re
import string
from datetime import date
import pdb
import os

# TODO: Factor this out
##################### REGEXES FOR PARSING ##############################
SECTION_RE = re.compile("[IV]+\.\s([a-zA-Z]+)\s+-\s+([a-zA-z]+)$")
# IN PROGRESS: Changing this for the new category parsing
CATEGORY_RE = re.compile("^\s*([0-9]+)\s.*$")
EINNAHMEN_RE = re.compile("([a-zA-Z]+)[\s']*([0-9]{2}\.[0-9]{2}\.[0-9]{4})\s*([,.0-9]+)")
AUSGABEN_RE = re.compile("(.*)([0-9]{2}\.[0-9]{2}\.[0-9]{4}).*-\s+([,.0-9]+)")
MY_SHARE = float("0.1667")
PROP_RE = re.compile("Liegenschaft.*[:](.*)$")
OWNER_RE = re.compile("Eigen.*[:](.*)$")

###################### STATICS FOR GLOBALS and DEFINITIONS ###############

#TODO: Factor out - for now makes parsing easier as we just need to OCR the ID"
TRANSLATIONS_DICT = {
        '40000':['Erlöse Mietzinse','Income from rent','Rent Received'],
        '40001':['Erlöse Mietzinse','Income from rent','Rent Received'],
        '40002':['Erlöse Mietzinse','Income from rent','Rent Received'],
        '40042':['Erlïöse Geschäftsraummiete','Income from rent commercial units','Rent Received'],
        '40061':['Erlöse Hauptmietzins frei vereinbart (ABGB)','Income from rent fixed rate','Rent Received'],
        '40202':['Erlöse Garagenmiete','Income from renting garage','Rent Received'],
        '40410':['Erlöse Gartenmiete','Income from rent garden units','Rent Received'],
        '57050':['Energiekosten - Leerstehung','Energy costs due to being vacant','TBC'],
        '71000':['Gebäude - Instandhaltung','Maintenance (eletrician/painter/cleaner/locksmith etc)','TBC'],
        '73000':['Rechts- und Beratungsaufwand','Legal fees','Legal Fees'],
        '74000':['Steuerberatungskosten','Tax accountancy fees','Accountancy Fees'],
        '40450':['Erlöse Waschküche','Income from laundromat','Rent Received'],
        '77000':['Versicherungschäden - Aufwendungen','Fees towards Insurance claims','TBC'],
        '78000':['Sonstige Aufwendungen 00%','Sundry expenses @0%','Sundry'],
        '78001':['Sonstige Aufwendungen 10%','Sundry expenses @10%','Sundry'],
        '78002':['Sonstige Aufwendungen 20%','Sundry expenses @20%','Sundry'],
        '79000':['Leerstehungsaufwand','Contribution due to being vacant','TBC'],
        '79200':['Vorsteuern - unecht steuerfreie Umsätze','Costs deducted pre-tax ','TBC'],
        '84000':['Bankzinsen','Bank interest','Other Income'],
        '84001':['Bankspesen','Bank transaction fees','TBC'],
        '84002':['Kapitalertragssteuer (KESt)','Capital Gains tax appreciation write-off','TBC'],
}



# Items PB are interested in
PBCAT_ARR = [
    'Rent Received',
    'Other Income',
    'Council Tax',
    'Water Rates',
    'Electricity Rates',
    'Insurance',
    'Ground Rent',
    'Repairs/ Maintenance',
    'Mortgage Interest',
    'Service Charge',
    'Agents Commission',
    'Other Agents Fees',
    'Legal Fees',
    'Accountancy Fees',
    'Advertising',
    'Gardening',
    'Travel/Milage',
    'Sundry',
]

#Helper to convert AT notation into date data_structure
def parse_date(d):
    #print(d)
    d = d.split(".")
    d = [int(x) for x in d]
    return date(d[2], d[1], d[0])

def make_category_ds(d):
    cat_ds = {}
    for k in d:
        c = Category(k)
        cat_ds[k] = c
    return cat_ds


#Takes the parsed dicts and turns them into data_structures for future use
def parse_ds(parsed):
    a = Account()
    a.owner = parsed["owner"]
    a.property = parsed["property"]
    sections = parsed["sections"]
    # HACK/TODO: Create DS for all Categories we know about
    defined_categories = make_category_ds(TRANSLATIONS_DICT)
    for section in sections:
        #print("Section is {0}".format(section))
        s = Section(section)
        a.sections.append(s)
        section = sections[section]
        #print(section)
        for category in section:
            #print("Category {0} for Section {1}".format(category, section))
            # Attempt to lookup the category ID
            if category in defined_categories:
                c = defined_categories[category]
                #c = Category(c)
                category = section[category]
                for item in category:
                    # Create an item and link it back to its parent category as this makes lookup easier later
                    c.items.append(Item(item["item"], item["date"], item["value"], c))
                s.categories.append(c)
            # If we can't find this category we skip it and warn
            else:
                print("Category '{0}' not found".format(category))
    
            print("ACCOUNTED FOR {0} {1}".format(a.owner, a.property))
    return a

# DS to represent a line item in the accounts
class Item:
    def __init__(self, item, date, value, parent_cat):
        self.item = item
        self.date = parse_date(date)
        self.value = float(value)
        self.parent_cat = parent_cat

    def __str__(self):
        return "{0}, {1}, {2}".format(self.item, self.date, self.value)

# DS to represent a portfolio of properties
class Account:
    def __init__(self):
        self.owner = ""
        self.property = ""
        self.sections = []

    def __str__(self):
        return self.sections

    def tosv(self, delim=","):
        output = ["Category{0}Item{0}Date{0}Value{0}MyShare{1}){0}".format(delim, MY_SHARE)]
        for s in self.sections:
            output.append("{1}{0}{0}{0}{0}\n".format(delim, s.name))
            for c in s.categories:
                for i in c.items:
                    date = "{0}/{1}/{2}".format(i.date.day, i.date.month, i.date.year)
                    output.append("{1}{0}{2}{0}{3}{0}{4}{0}{5}\n".format(delim, c.name, i.item, date, i.value, i.value*MY_SHARE))
        return output

    # Outputs delimeted view for PB i.e. For each month (row) all their categories summed
    def to_pb(self, delim=","):
        # We'd like a DS to build an index of their categories per month i.e. pb[month][cat] = items 
        # Then we can both do detailed breakdown and/or calculate the sum of these items

        # First step is to get all items across all categories per month




# DS to represent all types of category in AT tax and to map it to a PB cat
class Category:
    def __init__(self, at_code):
        self.at_code = at_code
        self.name = "uninitialised {0}".format(at_code)
        self.translation = "unitialised"
        self.pb_cat = "uninitialised"
        self._initfields()
        self.items = []

    def _initfields(self):
        mapping = TRANSLATIONS_DICT[self.at_code]
        if mapping:
            self.name = mapping[0]
            self.translation = mapping[1]
            self.pb_cat = mapping[2]

# DS to represent major heading in accounts
class Section:
    def __init__(self, name):
        self.name = name
        self.categories = []

    def __str__(self):
        return self.name

# Helper to clean up and remove pointless . and ,
def sanitise_number(num):
    #print("Number {0}".format(num))
    num = num.replace(",", "")
    num = num.replace(".", "")
    num = "{0}.{1}".format(num[0:-2],num[-2])
    #print(num)
    return float(num)

# Helper to create data_structure for an accounting item TODO: Should this be the constructor of Item?
def build_item(m):
    #print("1:{0} 2:{1} 3:{2}".format(m.group(1), m.group(2), m.group(3)))
    num = sanitise_number(m.group(3))
    myshare = num*MY_SHARE
    return {"item": m.group(1), "date": m.group(2), "value": num, "my_share": myshare}


###################################### PARSING OF OCRED TEXT ################################

# Parse a line item
def parse_item(line):
    item = {}
    # Check Einnahme
    m = EINNAHMEN_RE.match(line)
    if m:
        return build_item(m)
    # Check Ausgabe
    m = AUSGABEN_RE.match(line)
    if m:
        return build_item(m)

# Parse an entire category
def parse_category(lines):
    items = []
    for line in lines:
        line = ''.join(x for x in line if x in string.printable)
        item = parse_item(line)
        if item:
            items.append(item)
    return items

# Parse a section
def parse_section(lines):
    #print(lines)
    categories = {}
    # TODO: Change to ID
    category_name = ""
    category_text = []
    for line in lines:
        line.strip()
        # EXTRACT CATEGORY ID
        m = CATEGORY_RE.match(line)
        # IF this is a new section process the last and start again
        if m:
#            print("We matched Category {0} - {1}".format(line, m.group(1)))
#            print("Calling parse_cateogy for {0}".format(category_text))
            items = parse_category(category_text)
            merged = []
            # If we are already building this we need to merge
            if category_name in categories.keys():
                print("=========== WE EXIST ALREADY {0}".format(category_name))
                merged = categories[category_name] + items
            # else we start a new list
            else:
                merged = items
            # Either way we update the dict with all items we found for this cat
            categories[category_name] = merged
            category_text = []
            category_name = m.group(1)
        # Add the current line to the current cateogry (indepent of if we are in a new category now or not)
        category_text.append(line)

    # DICT of category name to list of all line items
    # TODO: category_name is really an ID now
    categories[category_name] = parse_category(category_text)
    return categories

# Parse an entire property
def parse_abrechnung(lines):
    owner = "Charmander"
    prop = "Pallet Town"
    named = False
    tagged = False
    sections = {}
    section_name = ""
    section_text = []
    for line in lines:
        line = line.strip()
  #print(line)
  #line = clean_latin1(line)
  #line = ''.join(x for x in line if x in string.printable)
        line = line.replace('\xe2\x80\x94','-')
  #print(line)
  # Check if we hit the section start
        if not named:
            m = OWNER_RE.match(line)
            if m:
                named = True
                owner = m.group(1).strip()
        if not tagged:
            m = PROP_RE.match(line)
            if m:
                #print("PROP_RE {0}".format(line))
                tagged = True
                prop = m.group(1).strip()
        # Check for section heading
        m = SECTION_RE.match(line)
        if m:
          #print("About to parse {0}".format(section_name))
          sections[section_name] = parse_section(section_text)
          section_text = []
          section_name = m.group(1)
        section_text.append(line)
    #At EOF process text in buffer as a section
    sections[section_name] = parse_section(section_text)
    print("OWNER: {0} PROPERTY: {1}".format(owner, prop))
    return {"owner": owner, "sections": sections, "property": prop}

###################################### OUTPUT AND FORMATTING ########################

def pretty_output(parsed):
    for section in parsed:
        print "===={0}===".format(section)
        section = parsed[section]
        for category in section:
            print "++++ {0} ++++".format(category)
            category = section[category]
            for item in category:
                print item

###################################### READ RAW INPUT FROM FILES #####################

# Reads OCRed text and orchestrates parsing
def extract_and_ds(ocr_name):
    account = None
    with open(ocr_name, "rb") as f:
        lines = f.readlines()
        parsed = parse_abrechnung(lines)
        account = parse_ds(parsed)
    return account

# Takes the PDFs and manages them being OCRED
def convert_and_ocr(file_name, pages):
    file_name = file_name.split(".")[0]
    d = "tmp"
    fpath = "{0}/{1}ocr.txt".format(d, file_name)
    if os.path.isfile(fpath):
        return fpath
    print("file:{0} pages:{1}".format(file_name, pages))
    #pdftk abrechnung.pdf cat 7-9 output abrechnung_lang.pdf
    c = "pdftk {1}.pdf cat {2} output {0}/{1}lang".format(d, file_name, pages)
    print(c)
    os.system(c)
    #convert -density 300 abrechnung_lang.pdf -depth 8 -strip -background white -alpha off file.tiff
    c = "convert -density 300 {0}/{1}lang -depth 8 -strip -background white -alpha off {0}/{1}.tiff".format(d, file_name)
    print("Convert {0}".format(c))
    os.system(c)
    #tesseract file.tiff output.text -psm 6
    c = "tesseract {0}/{1}.tiff {0}/{1}ocr -psm 6".format(d, file_name)
    print("OCR {0}".format(c))
    os.system(c)
    return fpath

# Outputs the account in long form
def output_long_csv(accounts):
    for acc in accounts:
        print(acc.property)
        name = acc.property
        tsv = acc.tosv(",")
        #print(tsv)
        with open("output-long/{0}.csv".format(name), "w+") as w:
            w.writelines(tsv)

# Calculates PB per month and outputs in a format useful for that
def output_per_pb(accounts):
    # Loop through each property in the account
    for property in accounts:
        name = acc.property
        tsv = acc.to_pb(",")
        # Output the file as CSV
        with open("output-PB/{0}.csv".format(name), "w+") as w:
            w.writelines(tsv)



# MAIN FUNCTION
if __name__ == "__main__":
    print("Let's go")
    # Read config
    cfg = []
    accounts = []
    
    # TODO: HACKY AT THIS LOCATION -INIT CATEGORY DICT
    #init_cat()
    
    # READ CONFIG AND PROCESS PDFS
    with open("file_config", "rb") as config:
        lines = config.readlines()
        for line in lines:
            line = line.strip().split(":")
            cfg.append((line[0], line[1]))
        for i in cfg:
            file_name = i[0]
            pages = i[1]
            ocr_name = convert_and_ocr(file_name, pages)
            acc = extract_and_ds(ocr_name)
            print("{0}".format(acc.owner))
            accounts.append(acc)
    # Orchestrate output as CSV for all properties in portfolio
    output_long_csv(accounts)
    
