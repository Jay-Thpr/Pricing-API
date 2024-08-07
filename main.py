from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

# Load structured data from file
with open('structured_pricing_data.json', 'r') as file:
    structured_data = json.load(file)

# Define the request model
class PricingRequest(BaseModel):
    cpu_type: str
    region: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Pricing API"}

@app.post("/get_price/")
def get_price(request: PricingRequest):
    cpu_type = request.cpu_type
    region = request.region

    for table in structured_data:
        if table.get("header") and "Machine type" in table["header"]:
            for row in table["rows"]:
                if row[0] == cpu_type:
                    price_data = row[-1]
                    if isinstance(price_data, dict):
                        price_by_region = price_data.get("priceByRegion", {})
                        if region in price_by_region:
                            return {"price": price_by_region[region]}
                    raise HTTPException(status_code=404, detail="Price not found for the specified CPU type or region")

    raise HTTPException(status_code=404, detail="Table with specified CPU type not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
