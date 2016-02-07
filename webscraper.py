import requests
from html.parser import HTMLParser
import re

class TableHTMLParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.is_tabel = False
        self.current_tag = None
        self.current_data = None
        self.current_row = []
        self.current_table = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.is_tabel = True
        if self.is_tabel:
            if tag == 'td' or tag == 'tr':
                self.current_tag = tag

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.current_tag = None
            self.current_table.append(self.current_row)
            self.current_row = []
        if tag == 'td':
            self.current_tag = None
            self.current_row.append(self.current_data)
            self.current_data = None
        if tag == 'table':
            self.is_tabel = False
            self.current_tag = None
            self.tables.append(self.current_table)
            self.current_table = []

    def handle_data(self, data):
        if self.current_tag == 'td':
            if self.current_data is None:
                self.current_data = data
            else:
                self.current_data += data

    def print_tables(self):
        for table  in self.tables:
            print("[")
            for row in table:
                try:
                    print ("    " + str(row))
                except:
                    print('-------------------------------------------------------------------------------')
            print("]")
            print ("\n")

    def fix_tables(self):
        for table in self.tables:
            for row in table:
                if len(row) == 0:
                    table.remove(row)
            if len(table) == 0:
                self.tables.remove(table)
            if table[0][0] == '\n\n':
                self.tables.remove(table)
            for row in table:
                for i, elem in enumerate(row):
                    row[i] = str(row[i])
                    if type(row[i]) == type("helo"):
                        row[i] = row[i].replace(',', '')
                        row[i] = row[i].replace("\xa0", '')
                        p= re.compile('\[\d+\]')
                        row[i] = p.sub('',row[i])
                        if row[i] == 'unknown' or row[i] == 'None':
                            row[i] = None
                    try:  # try to make a value numerical
                        row[i] = float(row[i])
                        if int(row[i]) == row[i]:
                            row[i] = int(row[i])
                    except:  # if it fails just keep it the type it was.
                        pass

def to_dict(table, collumns, identifier):
    """

    :param table:
    :param collumns:
    :param identifier:
    :return:
    :raise Exception:
    """
    d = dict()
    if identifier not in collumns:
        raise Exception
    for row in table:
        if len(row) != len(collumns):
            raise Exception
        temp = dict()
        for i, x in enumerate(row):
            temp[collumns[i]] = x
        d[temp[identifier]] = temp
    return d

def print_table(table):
    print('[')
    try:
        for key in table.keys():
            print('\t'+str(table[key]))
    except AttributeError:
        for row in table:
            print('\t' + str(row))
    print(']')
