from datetime import datetime
from bs4 import BeautifulSoup
import requests
from flask import Flask, request, jsonify
import json
import urllib3
from werkzeug.exceptions import BadRequest

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


@app.route("/get_data", methods=['POST'])
def post():

    my_placeId = None
    my_city = None
    params = request.json
    place = params.get('place')
    type = params.get('type', 'daily')
    time = params.get('time', datetime.now())
    response = None

    if not place:
        raise BadRequest()

    resp = requests.get('https://api.weather.com/v3/location/search?apiKey=d522aa97197fd864d36b418f39ebb323&format='
                        'json&language=en-IN&locationType=locale&query={}'.format(place), verify=False)

    print(resp)
    if resp.status_code == 200:

        content = resp.content
        string_content = content.decode("utf-8")
        jdata = json.loads(string_content)
        address_list = jdata.get('location').get('address')
        place_id_list = jdata.get('location').get('placeId')
        if len(address_list) > 0:
            my_city = address_list[0]  # program is designed to take only the first city it gets in the json data
        if len(place_id_list) > 0:
            my_placeId = place_id_list[0]   # program is designed to take only the first place_id corresponding
                                            # to the first city
                                            # received in the json data

        if type == 'today':
            response = today(type, my_placeId, my_city)
        elif type == 'hourbyhour':
            response = multi(type, my_placeId, my_city)
        elif type == '5day':
            response = multi(type, my_placeId, my_city)
        elif type == 'tenday':
            response = multi(type, my_placeId, my_city)
        elif type == 'weekend':
            response = weekend(type, my_placeId, my_city)

        return jsonify(response)

    else:
        return jsonify('Bad Request')

# Today weather data
def today(type, my_placeId, my_city):
    response = requests.get('https://weather.com/en-IN/weather/{}/l/{}'.format(type, my_placeId))

    soup = BeautifulSoup(response.text, 'html.parser')

    posts = soup.find_all(
        class_='today_nowcard')
    for post in posts:
        list = []
        title = soup.title.get_text()
        name = soup.title.name
        p = soup.find_all('p')[1].get_text()
        city = soup.find(class_='h4 today_nowcard-location').get_text()
        time_stamp = soup.find(class_='today_nowcard-timestamp').get_text()
        temperature = soup.find(class_='today_nowcard-temp').get_text().replace('\n', '')
        phrase = soup.find(class_='today_nowcard-phrase').get_text().replace('\n', '')
        feels_like_temp = soup.find(class_='deg-feels').get_text()
        list3 = []
        data1 = soup.find('div', {'class': 'today_nowcard-hilo'})
        for da in data1.find_all(class_='btn-text'):
            for sa in data1.find_all(class_='deg-hilo-newcard'):
                gr = da.get_text()
                br = sa.get_text()
                list3.append(gr + ':' + br)
        data = soup.find('div', {'class': 'today_nowcard-sidecar component panel'})
        list2 = []
        for tr in data.find_all('tr'):
            heading = tr.th.get_text()
            value = tr.td.get_text()
            list2.append(heading + ':' + value)

        links = soup.find_all('a', {'class': 'cta-link'})
        list4 = []
        for link in links:
            link_type = link.get_text()
            url = link['href']
            list4.append(link_type + ':' + url)

        list.append({'title': title, 'city': city, 'time_stamp': time_stamp, 'phrase': phrase,
                     'feel_like_temperature': feels_like_temp, 'actual_temperature': temperature,
                     'high_low': list3, 'data': list2,
                     'link': list4})
        return {'City Name': my_city, 'Data': list}


# hourly, 5 day, 10 day weather data
def multi(type, my_placeId, my_city):
    response = requests.get(
        'https://weather.com/en-IN/weather/{}/l/{}'.format(type, my_placeId))
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find('table', class_='twc-table')
    header = posts.find_all('th')
    headers = [head.get_text().replace('\n', '') for head in header]

    table_rows = posts.find('tbody').find_all('tr')
    results = [
        {headers[i]: cell.get_text().replace('\n', '') for i, cell in enumerate(row.find_all("td", {"headers": True}))}
        for row in table_rows]
    return {'City Name': my_city, 'Weather Data': results}


# Weekend weather data
def weekend(type, my_placeId, my_city):
    headers_list = []
    response = requests.get('https://weather.com/en-IN/weather/{}/l/{}'.format(type, my_placeId))
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find('div', class_='weather-table')
    for post in posts.find_all('span', class_=True):
        headers = post.get_text()
        headers_list.append(headers)
    posts2 = soup.find('div', class_='forecast ten-day weather-table')
    rows = posts2.find_all('div')
    results1 = [{headers_list[i]: cell.get_text().replace('\n', '') for i, cell in
                 enumerate(row.find_all(class_='weather-cell'))} for row in rows]
    results2 = []
    posts2 = soup.find_all('div', class_='forecast ten-day weather-table')
    for post in posts2:
        rows = post.find_all('div')
        results2 = [{headers_list[i]: cell.get_text().replace('\n', '') for i, cell in
                     enumerate(row.find_all(class_='weather-cell'))} for row in rows]
    return {'City Name': my_city, 'this-weekend': results1, 'next-weekend': results2}


if __name__ == "__main__":
    app.run()