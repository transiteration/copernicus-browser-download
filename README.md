### How to Download the Data from the Copernicus Browser

***Arguments to run the script:***

-u, --username: Copernicus username
-p, --password: Copernicus password
-b, --bbox: Bounding box in format min_lon min_lat max_lon max_lat
-s, --start_date: Start date in format YYYY-MM-DD
-e, --end_date: End date in format YYYY-MM-DD
-c, --cloud_cover: Cloud coverage value threshold 
-d, --download_path: Path to store downloaded files

Example of the run command with specified arguments:

```
python3 copernicus.py \
-u YOUR_USERNAME \
-p YOUR_PASSWORD \
-b "125.70481645582738 34.20968548454498 126.9345925072153 35.225027697578504" \
-s 2024-01-01 \
-e 2024-01-02 \
-c 20.0 \
-d ./data
```