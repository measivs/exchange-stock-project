import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def company_names():
    companies = []
    h = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    url = 'https://finance.yahoo.com/most-active?count=50&offset=0'
    logging.debug(f"Fetching URL: {url}")
    r = requests.get(url, headers=h)
    content = r.text

    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', {'class': 'W(100%)'})
    if not table:
        logging.error("Table not found on the page.")
        return []

    rows = table.find_all('tr')
    for row in rows:
        cells = row.find('a', {'class': 'Fw(600) C($linkColor)'})
        if cells:
            company_name = cells.text.strip()
            companies.append(company_name)

    logging.debug(f"Found companies: {companies}")
    return companies

def analyzing(company_list):
    company_data = []
    for company in company_list:
        h = {
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
        url = f"https://finance.yahoo.com/quote/{company}/analysis/"
        logging.debug(f"Fetching URL for analysis: {url}")
        r = requests.get(url, headers=h)
        content = r.text

        soup = BeautifulSoup(content, 'html.parser')
        section = soup.find('section', {'data-testid': 'revenueEstimate'})

        if section:
            rows = section.find_all('tr')
            data = {'Company': company}
            for row in rows:
                cells = row.find_all('td')
                if cells:
                    values = [cell.text.strip() for cell in cells]
                    if len(values) >= 4 and values[0] not in ['No. of Analysts', 'Year Ago Sales']:
                        data[values[0]] = values[3]

            company_data.append(data)
        else:
            logging.warning(f"Could not find revenue estimate section for company {company}")

    logging.debug(f"Analyzed company data: {company_data}")
    return company_data

if __name__ == '__main__':
    try:
        companies = company_names()
        if companies:
            analyzed_data = analyzing(companies)
            print(analyzed_data)
        else:
            logging.error("No companies found.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
