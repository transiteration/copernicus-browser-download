import os
import argparse
import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime
from shapely.geometry import shape

def get_keycloak(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data=data,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def download_tiles(username: str, password: str, bbox: str, start_date: str, end_date: str, cloud_cover: float, download_path: str):
    bbox_coords = list(map(float, bbox.split()))
    ft = f"POLYGON(({bbox_coords[0]} {bbox_coords[1]}, {bbox_coords[0]} {bbox_coords[3]}, {bbox_coords[2]} {bbox_coords[3]}, {bbox_coords[2]} {bbox_coords[1]}, {bbox_coords[0]} {bbox_coords[1]}))"
    start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    data_collection = "SENTINEL-2"
    url = (
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter="
        f"Collection/Name eq '{data_collection}' and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and "
        f"att/OData.CSC.DoubleAttribute/Value le {cloud_cover}) and " 
        f"OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and "
        f"ContentDate/Start gt {start_date}T00:00:00.000Z and "
        f"ContentDate/Start lt {end_date}T00:00:00.000Z&$count=True&$top=1000"
    ) 
    json = requests.get(url).json()
    p = pd.DataFrame.from_dict(json["value"])

    if p.shape[0] > 0:
        p["geometry"] = p["GeoFootprint"].apply(shape)
        productDF = gpd.GeoDataFrame(p).set_geometry("geometry")
        print(f"Total tiles found: {len(productDF)}")
        productDF["identifier"] = productDF["Name"].str.split(".").str[0]

        if len(productDF) == 0:
            print("No tiles found for the specified date range")
        else:
            session = requests.Session()
            keycloak_token = get_keycloak(username, password)
            session.headers.update({"Authorization": f"Bearer {keycloak_token}"})

            for _, feat in productDF.iterrows():
                try:
                    product_id = feat["Id"]
                    product_name = feat["Name"]
                    identifier = feat["identifier"]
                    download_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
                    response = session.get(download_url, allow_redirects=False)
                    
                    while response.status_code in (301, 302, 303, 307):
                        download_url = response.headers["Location"]
                        response = session.get(download_url, allow_redirects=False)

                    file_response = session.get(download_url, verify=False, allow_redirects=True)
                    with open(os.path.join(download_path, f"{identifier}.zip"), "wb") as f:
                        f.write(file_response.content)
                    print(f"Downloaded {product_name}")
                except Exception as e:
                    print(f"Problem downloading {product_name}: {e}")
    else:
        print("No data found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Sentinel-2 tiles from Copernicus Open Access Hub.")
    parser.add_argument("-u", "--username", type=str, required=True, help="Copernicus username")
    parser.add_argument("-p", "--password", type=str, required=True, help="Copernicus password")
    parser.add_argument("-b", "--bbox", type=str, required=True, help="Bounding box in format: min_lon min_lat max_lon max_lat")
    parser.add_argument("-s", "--start_date", type=str, required=True, help="Start date in format YYYY-MM-DD")
    parser.add_argument("-e", "--end_date", type=str, required=True, help="End date in format YYYY-MM-DD")
    parser.add_argument("-c", "--cloud_cover", type=float, required=True, help="Start date in format YYYY-MM-DD")
    parser.add_argument("-d", "--download_path", type=str, required=True, help="Path to store downloaded files")

    args = parser.parse_args()
    download_tiles(username=args.username,
                   password=args.password,
                   bbox=args.bbox,
                   start_date=args.start_date,
                   end_date=args.end_date,
                   cloud_cover=args.cloud_cover,
                   download_path=args.download_path)
