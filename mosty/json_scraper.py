import json
import requests
import zipfile, os, pandas as pd

def json_scraper(headers, url, file_name, chunk_size=128):
    response = requests.request("GET", url, headers=headers, stream=True)
    with open(file_name, 'wb') as outfile:
        for chunk in response.iter_content(chunk_size=chunk_size):
            outfile.write(chunk)


def unzip_folder(filename_zip, directory_json):
    with zipfile.ZipFile(filename_zip, 'r') as zip_ref:
        zip_ref.extractall(directory_json)


def extract_jsons_to_csv(directory_json, csv_file):
    data = []
    for file in os.listdir(directory_json):
        df_file = pd.read_json(directory_json+'/'+file, orient='records')
        data.append(df_file)
    df = pd.concat(data)
    df.to_csv(csv_file, encoding='utf-8')
        
            




token_file = '../data/token.json'
mosty_url = 'https://www.hlidacstatu.cz/api/v2/dump/dataset.stav-mostu'
zip_file = "../data/mosty_dump.zip"
json_dir = "../data/mosty_json"
csv_file = "../data/mosty_ids_dump.csv"

f = open(token_file)
json_data = json.load(f)
f.close()


json_scraper(headers={'Authorization': 'Token '+json_data["token_hlidac_statu"]}, url=mosty_url, file_name=zip_file)

unzip_folder(zip_file, json_dir)

extract_jsons_to_csv(json_dir, csv_file)



