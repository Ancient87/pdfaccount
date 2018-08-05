#!/usr/bin/python
#coding=utf-8

import pdftotext
import re
import string
from datetime import date
import pdb
import os

SECTION_RE = re.compile("[IV]+\.\s([a-zA-Z]+)\s+-\s+([a-zA-z]+)$")
CATEGORY_RE = re.compile("[0-9]+\s(.*)$")
EINNAHMEN_RE = re.compile("([a-zA-Z]+)\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})\s*([,.0-9]+)")
AUSGABEN_RE = re.compile("(.*)([0-9]{2}\.[0-9]{2}\.[0-9]{4}).*-\s+([,.0-9]+)")
MY_SHARE = float("0.1667")
PROP_RE = re.compile("Liegenschaft.*[:](.*)$")
OWNER_RE = re.compile("Eigen.*[:](.*)$")

def parse_date(d):
    #print(d)
    d = d.split(".")
    d = [int(x) for x in d]
    return date(d[2], d[1], d[0])

def parse_ds(parsed):
    a = Account()
    a.owner = parsed["owner"]
    a.property = parsed["property"]
    sections = parsed["sections"]
    for section in sections:
        s = Section(section)
        a.sections.append(s)
        section = sections[section]
        for category in section:
            c = Category(category)
            category = section[category]
            for item in category:
                c.items.append(Item(item["item"], item["date"], item["value"]))
            s.categories.append(c)
    print("ACCOUNTED FOR {0} {1}".format(a.owner, a.property))
    return a

class Item:

    def __init__(self, item, date, value):
        self.item = item
        self.date = parse_date(date)
        self.value = float(value)

    def __str__(self):
        return "{0}, {1}, {2}".format(self.item, self.date, self.value)

class Account:
    def __init__(self):
        self.owner = ""
        self.property = ""
        self.sections = []

    def __str__(self):
        return self.sections

    def totsv(self):
        output = ["Category\tItem\tDate\tValue\tMyShare{0})\n".format(MY_SHARE)]
        for s in self.sections:
            output.append("{0}\t\t\t\t\n".format(s.name))
            for c in s.categories:
                for i in c.items:
                    date = "{0}/{1}/{2}".format(i.date.day, i.date.month, i.date.year)
                    output.append("{0}\t{1}\t{2}\t{3}\t{4}\n".format(c.name, i.item, date, i.value, i.value*MY_SHARE))
        return output




class Category:
    def __init__(self, name):
        self.name = name
        self.items = []

class Section:
    def __init__(self, name):
        self.name = name
        self.categories = []

    def __str__(self):
        return self.name


LATIN_1_CHARS = (
        ('\xe2\x80\x99', "'"),
        ('\xc3\xa9', 'e'),
        ('\xe2\x80\x90', '-'),
        ('\xe2\x80\x91', '-'),
        ('\xe2\x80\x92', '-'),
        ('\xe2\x80\x93', '-'),
        ('\xe2\x80\x94', '-'),
        ('\xe2\x80\x94', '-'),
        ('\xe2\x80\x98', "'"),
        ('\xe2\x80\x9b', "'"),
        ('\xe2\x80\x9c', '"'),
        ('\xe2\x80\x9c', '"'),
        ('\xe2\x80\x9d', '"'),
        ('\xe2\x80\x9e', '"'),
        ('\xe2\x80\x9f', '"'),
        ('\xe2\x80\xa6', '...'),
        ('\xe2\x80\xb2', "'"),
        ('\xe2\x80\xb3', "'"),
        ('\xe2\x80\xb4', "'"),
        ('\xe2\x80\xb5', "'"),
        ('\xe2\x80\xb6', "'"),
        ('\xe2\x80\xb7', "'"),
        ('\xe2\x81\xba', "+"),
        ('\xe2\x81\xbb', "-"),
        ('\xe2\x81\xbc', "="),
        ('\xe2\x81\xbd', "("),
        ('\xe2\x81\xbe', ")")
        )


def clean_latin1(data):
    try:
        return data.encode('utf-8')
    except UnicodeDecodeError:
        #print(data)
        data = data.decode('iso-8859-1')
        for _hex, _char in LATIN_1_CHARS:
            data = data.replace(_hex, _char)
        return data.encode('utf8')

def sanitise_number(num):
    #print("Number {0}".format(num))
    num = num.replace(",", "")
    num = num.replace(".", "")
    num = "{0}.{1}".format(num[0:-2],num[-2])
    #print(num)
    return float(num)

def build_item(m):
    print("1:{0} 2:{1} 3:{2}".format(m.group(1), m.group(2), m.group(3)))
    num = sanitise_number(m.group(3))
    myshare = num*MY_SHARE
    return {"item": m.group(1), "date": m.group(2), "value": num, "my_share": myshare}

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

def parse_category(lines):
    items = []
    for line in lines:
        line = ''.join(x for x in line if x in string.printable)
        item = parse_item(line)
        if item:
            items.append(item)
    return items

def parse_section(lines):
    #print(lines)
    categories = {}
    category_name = ""
    category_text = []
    for line in lines:
        line.strip()
        m = CATEGORY_RE.match(line)
        if m:
            print(line)
            categories[category_name] = parse_category(category_text)
            category_text = []
            category_name = m.group(1)
        category_text.append(line)

    categories[category_name] = parse_category(category_text)
    return categories

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
                print("PROP_RE {0}".format(line))
                tagged = True
                prop = m.group(1).strip()
        m = SECTION_RE.match(line)
        if m:
          print("About to parse {0}".format(section_name))
          sections[section_name] = parse_section(section_text)
          section_text = []
          section_name = m.group(1)
        section_text.append(line)
    #EOF
    sections[section_name] = parse_section(section_text)
    print("OWNER: {0} PROPERTY: {1}".format(owner, prop))
    return {"owner": owner, "sections": sections, "property": prop}

def pretty_output(parsed):
    for section in parsed:
        print "===={0}===".format(section)
        section = parsed[section]
        for category in section:
            print "++++ {0} ++++".format(category)
            category = section[category]
            for item in category:
                print item

def extract_and_ds(ocr_name):
    account = None
    with open(ocr_name, "rb") as f:
        lines = f.readlines()
        parsed = parse_abrechnung(lines)
        account = parse_ds(parsed)
    return account

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


if __name__ == "__main__":
    print("Let's go")
    # Read config
    cfg = []
    accounts = []
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
    for acc in accounts:
        print(acc.property)
        name = acc.property
        tsv = acc.totsv()
        #print(tsv)
        with open("{0}.tsv".format(name), "w+") as w:
            w.writelines(tsv)

