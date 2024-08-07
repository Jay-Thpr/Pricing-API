from bs4 import BeautifulSoup
import requests
import json
import ast

URL = "https://cloud.google.com/compute/all-pricing?authuser=1"
page = requests.get(URL)

if page.status_code == 200:
    soup = BeautifulSoup(page.content, 'html.parser')
else:
    print("Failed to retrieve the page.")
    exit()

pricing_tables = soup.find_all('cloudx-pricing-table')

if not pricing_tables:
    print("No cloudx-pricing-table elements found.")
    exit()

structured_data = []

for index, table in enumerate(pricing_tables):
    if 'layout' not in table.attrs:
        print(f"Table {index + 1} does not have a 'layout' attribute.")
        continue

    layout_str = table['layout']
    
    try:
        layout_dict = ast.literal_eval(layout_str)
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing layout string for table {index + 1}: {e}")
        continue

    table_data = {
        "header": layout_dict.get('rows', [])[0].get('cells', []),
        "rows": []
    }
    
    rows = layout_dict.get('rows', [])[1:]

    for row in rows:
        cells = row.get('cells', [])
        if len(cells) > 3 and isinstance(cells[3], (dict, str)):
            price_by_region_str = cells[3]
            try:
                if isinstance(price_by_region_str, str):
                    price_by_region = json.loads(price_by_region_str)
                else:
                    price_by_region = price_by_region_str
            except (json.JSONDecodeError, TypeError):
                print(f"Error parsing price_by_region: {price_by_region_str}")
                continue
            cells[3] = price_by_region
        table_data["rows"].append(cells)

    structured_data.append(table_data)

# Save structured data to a JSON file
with open('structured_pricing_data.json', 'w') as file:
    json.dump(structured_data, file, indent=4)

print(f"Extracted data for {len(structured_data)} tables.")

def get_cost(cpus, memory, region):
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

# Example usage

cpus = 4
memory = 15
region = "useast1"
print(get_cost(cpus, memory, region))