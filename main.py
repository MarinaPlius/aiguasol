from fastapi import FastAPI, status, Query, HTTPException, Depends
import os
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np
import json
import dateutil.parser as parser
from scipy.fft import fft, fftfreq

import matplotlib.pyplot as plt
from io import BytesIO
from starlette.responses import StreamingResponse

# load enviroment variables
load_dotenv()


app = FastAPI(title="Real Electricity Demand")

def common_parameters(item_id="1293", start_date="2018-09-02", end_date="2018-10-06", time_trunc: str = Query("hour", description="Accepted values:  `five_minutes`, `ten_minutes`, `fifteen_minutes`, `hour`, `day`, `month`, `year`.")):
	"""common parameters for the post methods"""
	return {"item_id": item_id, "start_date": start_date, "end_date": end_date, "time_trunc": time_trunc}

class Data():

	def __init__(self, params):
		self.params = params
		self.df = self.load_data()

	def load_data(self):
		"""
		make sure to add "PERSONAL_TOKEN" in env file!
		gets data through API
		returns data as dataframe
		"""

		# get personal token for API access from env file
		personal_token = os.getenv('PERSONAL_TOKEN')
		url = os.getenv("URL")

		# pass parameters
		headers = {'x-api-key': personal_token}
		url = url + str(self.params["item_id"])

		# validate dates
		try:
			self.params["start_date"] = parser.parse(self.params["start_date"]).isoformat()
			self.params["end_date"] = parser.parse(self.params["end_date"]).isoformat()
		except ParserError:
			raise HTTPException(status_code=422, detail="Incorrect date format!")

		# pass params to API
		self.params.pop("item_id")
		params = self.params

		# get and read data
		response = requests.get(url ,params=params , headers=headers)
		data = response.json()["indicator"]

		return pd.json_normalize(data, record_path= ["values"])


@app.get("/")
def root():
	"""home page redirects to docs"""
	return "http://localhost:8000/docs"

@app.get("/health", status_code=status.HTTP_200_OK)
def check_health():
	"""checks status of API"""
	return "status is Ok!"

@app.post("/fft_json") 
async def get_fft(params: dict = Depends(common_parameters)):
	"""apply Fast Fourier Transform to data
	returns json with data as array
	"""
	# load data
	data = Data(params)

	# transform to FFT
	yf = np.abs(fft(data.df["value"].to_numpy()))

	return json.dumps(yf.tolist())

@app.post("/visualize_demand") 
async def visualize_demand(params: dict = Depends(common_parameters)):
	"""
	returns a data plot as image
	"""
	# load data
	data = Data(params)
	
	# plot demand in time
	graph = plt.plot(data.df["datetime"], data.df["value"])

	# create a buffer to store image data
	buf = BytesIO()
	plt.savefig(buf, format="png")
	buf.seek(0)
        
	return StreamingResponse(buf, media_type="image/png")

@app.post("/visualize_fft") 
async def visualize_demand(params: dict = Depends(common_parameters)):
	"""
	returns plot of data applied FFT as image
	"""
	# load data
	data = Data(params)

	# transform to FFT
	yf = np.abs(fft(data.df["value"].to_numpy()))
	
	# plot demand in time
	graph = plt.plot(np.abs(yf)[1:])

	# create a buffer to store image data
	buf = BytesIO()
	plt.savefig(buf, format="png")
	buf.seek(0)
        
	return StreamingResponse(buf, media_type="image/png")





