import json
import requests
import zipfile, os, pandas as pd, re
import geopandas as gpd
from shapely.geometry import Point
import http.client
from tqdm import tqdm

def map_objects_scraper(filename):
    url = 'bms.clevera.cz'
    conn = http.client.HTTPConnection(host=url)
    headers = {'Content-type': 'application/json'}
    content = {
        "bounds":{
            "epsg":"5514",
            "esri":"10267",
            "xmin":-991863.6,
            "xmax":-77136.4,
            "ymin":-1255189.7,
            "ymax":-896165
            },
        "layers": " Most",
        "zoomIndex":17
    }

    conn.request("POST", url='/api/assetregistermap/GetMapAllObjects?t=1&d=0', body=json.dumps(content), headers=headers)
    response = conn.getresponse()
    print(response.status)
    data = response.read().decode()
    open(filename, 'w').write(data)
    

def json_bridge_scraper(headers, url, file_name, bridge):
    response = requests.request("GET", url, headers=headers)
    json_data = response.json()
    
    bridge_data = [parse_bridge_data(json_data['o'], bridge)]
    try:
        with open(file_name, 'w', encoding='utf-8') as outfile:
            json.dump(bridge_data, outfile, ensure_ascii=False, indent=4)
    except:
        print("No valid data for", url)


def parse_bridge_data(data, bridge):
    bridge['Jmeno'] = data["n"]
    bridge['MistniNazev'] = data["m"]
    bridge['Oznaceni'] = data["c"]
    spravce = data["sl"].split('|')
    bridge['SpravaOrganizace'] = spravce[0]
    if len(spravce) > 1:
        bridge['SpravaStredisko'] = spravce[1]
    if len(spravce) > 2:
        bridge['SpravaProvozniUsek'] = spravce[2]

    if("s" in data and data["s"]):
        bridge['PopisStavu'] = data["s"]
        prefix = bridge['PopisStavu'].split(' ')[0]
        if prefix in status_prefix_table:
            bridge['Stav'] = status_prefix_table[prefix]

    if("p" in data and data["p"]):
        bridge['ProhlidkaPopis'] = data["p"]
        dat = data["p"].split(' ')
        if dat:
            bridge['PosledniProhlidka'] = dat[0]

    return bridge



def extract_jsons_to_csv(directory_json, csv_file):
    data = []
    for file in os.listdir(directory_json):
        df_file = pd.read_json(directory_json+'/'+file, orient='records')
        data.append(df_file)
    df = pd.concat(data)
    df.to_csv(csv_file, encoding='utf-8')
        
            

token_file = '../data/token.json'
bms_url = 'http://bms.clevera.cz/api/assetregistermap/GetMapObjekt?g='
zip_file = "../data/mosty_dump.zip"
json_dir = "../data/mosty_json_scraped/"
csv_file = "../data/mosty_ids_dump.csv"
map_objects_file = "../data/map_objects.json"

f = open(token_file)
json_data = json.load(f)
f.close()

status_prefix_table = json_data["status_prefix_table"]

def load_map_objects(map_objects_file):
    if os.path.exists(map_objects_file):
        print("Map objects file exists", map_objects_file)
        f = open(map_objects_file)
        map_objects = json.load(f)
        f.close()
    else:
        map_objects = map_objects_scraper(map_objects_file)

    return map_objects["MapObjects"]


def load_files(map_objects):

    for record in tqdm(map_objects):
        bridge = {
            "Id": record['g'],
            'GPS_Lat': record['x'],
            'GPS_Lng': record['y']
        }
        json_bridge_scraper(headers={}, url=bms_url+bridge['Id'], file_name=json_dir+bridge['Id']+".csv", bridge=bridge)



def concat_files_to_csv():
    bridges = []
    for file in tqdm(os.listdir(json_dir)):
        j = pd.read_json(json_dir+"/"+file, orient='columns')
        bridges.append(j)

    df = pd.concat(bridges)
    print(df.head())
    print(df.info())

    df.loc[:,"geometry"] = df.apply(lambda row: Point(row.GPS_Lat, row.GPS_Lng), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:5514")

    gdf.to_crs(crs='EPSG:4326', inplace=True)

    gdf.loc[:,"GPS_Lat"] = gdf.geometry.apply(lambda p: p.x)
    gdf.loc[:,"GPS_Lng"] = gdf.geometry.apply(lambda p: p.y)

    gdf.to_csv("../data/mosty_stav_scraped_all.csv")

map_objects = load_map_objects(map_objects_file)
load_files(map_objects)
concat_files_to_csv()










