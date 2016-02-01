import re

from tokens import phpsessid
import requests
import webscraper
login_url = 'http://www.jotihunt.net/groep/loginform.php'
def get_opdrachten():
    try:
        with requests.Session() as session:
            session.cookies.set('PHPSESSID', phpsessid)
            r = session.get('http://www.jotihunt.net/groep/opdrachten.php')
            scraper = webscraper.TableHTMLParser()
            scraper.feed(r.text)
            scraper.fix_tables()
            scraper.print_tables()
            with open('opdracht.log','w') as f:
                f.write(r.text)
            scraper.tables[0] = fix_opdrachten(scraper.tables[0])
            webscraper.to_dict(scraper.tables[0],[])
            return scraper.tables[0]

    except:
        return [], ['Inzendtijd']

def get_hunts():
    try:
        with requests.Session() as session:
            session.cookies.set('PHPSESSID', phpsessid)
            r = session.get('http://www.jotihunt.net/groep/hunts.php')
            scraper = webscraper.TableHTMLParser()
            scraper.feed(r.text)
            with open('hunts.log','w') as f:
                f.write(r.text)
            scraper.fix_tables()
            scraper.print_tables()
            return scraper.tables[0], []
    except KeyboardInterrupt:
        return []
def fix_opdrachten(table):
    for i,row in enumerate(table):
        table.remove(row)
        row[1] = row[1].split('\n')[1]
        p = re.compile('\t')
        row[1] = p.sub('', row[1])
        table.insert(i,row)
    return table
get_opdrachten()
get_hunts()