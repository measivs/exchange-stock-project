from flask import Flask, redirect, url_for, render_template, request, session
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HelloBTU'

companies = []
def company_names():
    h = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    url = 'https://finance.yahoo.com/most-active?count=50&offset=0'
    r = requests.get(url, headers=h)
    content = r.text

    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', {'class': 'W(100%)'})
    rows = table.find_all('tr')

    for row in rows:
        cells = row.find('a', {'class': 'Fw(600) C($linkColor)'})
        if cells:
            company_name = cells.text.strip()
            companies.append(company_name)

    return companies


def analyzing(company_list):
    company_data = []
    for company in company_list:
        h = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
        url = f"https://finance.yahoo.com/quote/{company}/analysis/"
        r = requests.get(url, headers=h)
        content = r.text

        soup = BeautifulSoup(content, 'html.parser')
        section = soup.find('section', {'data-testid': 'revenueEstimate'})
        rows = section.find_all('tr')

        data = {'Company': company}
        for row in rows:
            cells = row.find_all('td', {'class': 'svelte-17yshpm'})
            if cells:
                values = [cell.text.strip() for cell in cells]
                if values[0] != 'No. of Analysts' and values[0] != 'Year Ago Sales':
                    data[values[0]] = values[3]
                
        company_data.append(data)

    return company_data

# print(analyzing(company_names()))


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', data=companies)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        session['username'] = email
        return render_template('user.html')
    return  render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)


