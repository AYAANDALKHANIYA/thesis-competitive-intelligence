import json

data = json.load(open('openapi.json'))

out = open('audit_draft.md', 'w')

out.write('# 3. Complete API Endpoint Inventory\n\n')
out.write('| Method | Endpoint | Purpose | Request | Response | DB-backed | Frontend Ready | Notes |\n')
out.write('|---|---|---|---|---|---|---|---|\n')

for path, methods in data['paths'].items():
    for method, details in methods.items():
        summary = details.get('summary', '')
        
        # Get query parameters
        params = details.get('parameters', [])
        query_params = [p['name'] for p in params if p['in'] == 'query']
        req = "Query: " + ", ".join(query_params) if query_params else "None"
        
        # Get request body schema
        if 'requestBody' in details:
            req = "JSON Body"
            
        # Get response
        resp_schema = "Unknown"
        if 'responses' in details and '200' in details['responses']:
            content = details['responses']['200'].get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                if '$ref' in schema:
                    resp_schema = schema['$ref'].split('/')[-1]
                elif schema.get('type') == 'array' and '$ref' in schema.get('items', {}):
                    resp_schema = "Array[" + schema['items']['$ref'].split('/')[-1] + "]"
                elif schema.get('type') == 'object':
                    resp_schema = "Object"
                else:
                    resp_schema = str(schema.get('type', 'Unknown'))
        
        db_backed = "Yes" if "health" not in path else "No"
        ready = "Yes"
        
        out.write(f"| {method.upper()} | {path} | {summary} | {req} | {resp_schema} | {db_backed} | {ready} | |\n")


out.write('\n\n# 5. Exact Frontend Data Contracts\n\n')

schemas = data.get('components', {}).get('schemas', {})
for name, schema in schemas.items():
    # Skip ValidationError etc
    if 'ValidationError' in name: continue
    
    out.write(f"### {name}\n")
    out.write("```json\n{\n")
    props = schema.get('properties', {})
    for prop_name, prop_details in props.items():
        prop_type = prop_details.get('type', '')
        if 'anyOf' in prop_details:
            types = [t.get('type', '') for t in prop_details['anyOf']]
            if '$ref' in prop_details['anyOf'][0]:
                types[0] = prop_details['anyOf'][0]['$ref'].split('/')[-1]
            prop_type = " | ".join(types)
        elif '$ref' in prop_details:
            prop_type = prop_details['$ref'].split('/')[-1]
        elif prop_type == 'array' and '$ref' in prop_details.get('items', {}):
            prop_type = "Array[" + prop_details['items']['$ref'].split('/')[-1] + "]"
            
        out.write(f"  \"{prop_name}\": \"{prop_type}\",\n")
    out.write("}\n```\n\n")

out.close()
print("Draft generated.")
