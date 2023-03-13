from fastapi import FastAPI, status, Query, HTTPException
import os
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np
import json
import dateutil.parser as parser
from scipy.fft import fft, fftfreq

# load enviroment variables
load_dotenv()


app = FastAPI(title="Real Electricity Demand")
    

@app.get("/")
def root():
    return "http://localhost:8000/docs"

@app.get("/health", status_code=status.HTTP_200_OK)
def check_health():
    return "status is Ok!"

@app.post("/fft") 
def get_fft(item_id="1293", start_date="2018-09-02", end_date="2018-10-06", time_trunc: str = Query("hour", description="Accepted values:  `five_minutes`, `ten_minutes`, `fifteen_minutes`, `hour`, `day`, `month`, `year`.") ):
	# get personal token for API access from env file
	personal_token = os.getenv('PERSONAL_TOKEN')
	url = os.getenv("URL")

	# pass parameters
	headers = {'x-api-key': personal_token}
	url = url + str(item_id)

	# validate dates
	try:
		start_date = parser.parse(start_date).isoformat()
		end_date = parser.parse(end_date).isoformat()
	except ParserError:
		raise HTTPException(status_code=422, detail="Incorrect date format!")

	params = {"start_date":start_date, "end_date":end_date, "time_trunc":time_trunc}

	# get and read data
	response = requests.get(url ,params=params , headers=headers)
	data = response.json()["indicator"]
	df = pd.json_normalize(data, record_path= ["values"])

	# transform to FFT
	yf = np.abs(fft(df["value"].to_numpy()))

	return json.dumps(yf.tolist())



