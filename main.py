from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

# Load structured data from file
with open('structured_pricing_data.json', 'r') as file:
    structured_data = json.load(file)

@app.get("/")
def read_root():
    """
    Root endpoint.
    """
    return {"message": "Welcome to the Pricing API"}

@app.get("/get_price/")
def get_price(cpu_type: str, region: str):
    """
    Endpoint to get price by CPU type and region.
    """
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

def get_cost(cpus, memory, region):
    """
    Helper function to get cost by specifying the number of CPUs, memory, and region.
    """
    for table in structured_data:
        headers = table['header']
        if 'Machine type' in headers:
            for row in table['rows']:
                machine_type = row[0]
                row_cpus = int(row[1])
                row_memory = int(row[2].replace('GB', '').strip())
                price_info = row[3]
                
                if row_cpus == cpus and row_memory == memory:
                    cost = price_info.get('priceByRegion', {}).get(region)
                    if cost:
                        return f"The cost for machine type '{machine_type}' with {cpus} CPUs, {memory}GB memory in region '{region}' is {cost} USD."
                    else:
                        return f"No pricing data available for machine type '{machine_type}' in the specified region: {region}."
    return "No matching machine type found for the given specifications."

@app.get("/get_cost/")
async def api_get_cost(cpus: int, memory: int, region: str):
    """
    Endpoint to get cost by specifying the number of CPUs, memory, and region.
    """
    cost_info = get_cost(cpus, memory, region)
    if "No matching machine type found" in cost_info or "No pricing data available" in cost_info:
        raise HTTPException(status_code=404, detail=cost_info)
    return {"cost_info": cost_info}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
