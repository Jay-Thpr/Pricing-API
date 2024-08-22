from fastapi import FastAPI, HTTPException
import json

app = FastAPI()

# Load structured data from file
with open('structured_pricing_data.json', 'r') as file:
    structured_data = json.load(file)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cloud Pricing API"}

def extract_value(cell):
    """ Helper function to extract a value from a cell (handling dicts, strings, etc.) """
    if isinstance(cell, dict):
        return cell.get("value", None)
    return cell

def find_matching_machine_types(cpus: int, memory: float):
    matching_machine_types = []

    # Iterate through all tables in the structured data
    for table in structured_data:
        headers = table.get('header', [])
        if 'Machine type' in headers:
            for row in table.get('rows', []):
                try:
                    # Extract values using the helper function
                    machine_type = extract_value(row[0])
                    row_cpus = int(extract_value(row[1]))
                    row_memory = float(extract_value(row[2]).replace('GB', '').strip())
                    
                    # If the machine's CPU and memory match the input, add to the result
                    if row_cpus == cpus and abs(row_memory - memory) < 0.01:
                        matching_machine_types.append({
                            "machine_type": machine_type,
                            "cpus": row_cpus,
                            "memory_gb": row_memory,
                            "price_info": extract_value(row[3])
                        })
                except (ValueError, IndexError, TypeError) as e:
                    continue

    return matching_machine_types

def get_cost(cpus, memory, region):
    """ Helper function to get cost by specifying the number of CPUs, memory, and region """
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
                        return { "machine_type": machine_type, "cost": cost }
                    else:
                        return { "machine_type": machine_type, "cost": None }
    return { "error": "No matching machine type found for the given specifications." }

@app.get("/get_matching_machine_types/")
async def get_matching_machine_types(cpus: int, memory: float, scale: int):
    matching_machine_types = find_matching_machine_types(cpus, memory)
    
    if not matching_machine_types:
        raise HTTPException(status_code=404, detail=f"No machine types found for {cpus} CPUs and {memory}GB memory")
    
    regions = [
        "uscentral1", "uswest1", "useast1", "europewest2", "europewest3",
        "europecentral2", "europewest4", "europewest6", "europewest8",
        "europewest9", "europewest10", "europesouthwest1", "southamericaeast1",
        "southamericawest1", "asiasouth1", "asiasouth2", "northamericanortheast1",
        "northamericanortheast2", "australiasoutheast2", "australiasoutheast1",
        "europewest1", "asiaeast1", "asiasoutheast1", "asiasoutheast2",
        "useast4", "useast5", "uswest4", "asianortheast1", "asianortheast2",
        "europenorth1", "uswest2", "uswest3", "asiaeast2", "asianortheast3",
        "mewest1", "europewest12", "mecentral1", "mecentral2", "ussouth1",
        "africasouth1"
    ]
    
    result = []
    for machine in matching_machine_types:
        machine_type = machine['machine_type']
        costs = {}
        for region in regions:
            cost_info = get_cost(machine['cpus'], machine['memory_gb'], region)
            if "error" in cost_info:
                continue
            if cost_info['cost'] is not None:
                costs[region] = float(cost_info['cost']) * scale
        if costs:
            result.append({
                "machine_type": machine_type,
                "cpus": machine['cpus'],
                "memory_gb": machine['memory_gb'],
                "scaled_costs": costs
            })
    
    return {"matching_machine_types": result}

@app.get("/find_cheapest_region/")
async def find_cheapest_region(cpus: int, memory: float, quantity: int):
    matching_machine_types = find_matching_machine_types(cpus, memory)
    
    if not matching_machine_types:
        raise HTTPException(status_code=404, detail=f"No machine types found for {cpus} CPUs and {memory}GB memory")

    regions = [
        "uscentral1", "uswest1", "useast1", "europewest2", "europewest3",
        "europecentral2", "europewest4", "europewest6", "europewest8",
        "europewest9", "europewest10", "europesouthwest1", "southamericaeast1",
        "southamericawest1", "asiasouth1", "asiasouth2", "northamericanortheast1",
        "northamericanortheast2", "australiasoutheast2", "australiasoutheast1",
        "europewest1", "asiaeast1", "asiasoutheast1", "asiasoutheast2",
        "useast4", "useast5", "uswest4", "asianortheast1", "asianortheast2",
        "europenorth1", "uswest2", "uswest3", "asiaeast2", "asianortheast3",
        "mewest1", "europewest12", "mecentral1", "mecentral2", "ussouth1",
        "africasouth1"
    ]

    cheapest_region = None
    min_total_cost = float('inf')
    best_machine_type = None
    
    for machine in matching_machine_types:
        machine_type = machine['machine_type']
        for region in regions:
            cost_info = get_cost(machine['cpus'], machine['memory_gb'], region)
            if "error" in cost_info:
                continue
            if cost_info['cost'] is not None:
                total_cost = float(cost_info['cost']) * quantity
                if total_cost < min_total_cost:
                    min_total_cost = total_cost
                    cheapest_region = region
                    best_machine_type = machine_type
    
    if cheapest_region is None:
        raise HTTPException(status_code=404, detail="No pricing data available for the given specifications.")
    
    return {
        "machine_type": best_machine_type,
        "cheapest_region": cheapest_region,
        "total_cost": min_total_cost
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
