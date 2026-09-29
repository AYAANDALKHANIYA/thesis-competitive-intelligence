import requests, time, sys
print('Waiting for analysis 35...')
while True:
    try:
        r = requests.get('http://localhost:8000/api/v1/analysis/api/v1/analysis/35/status').json()
        status = r.get('status')
        print(f'Status: {status}')
        if status in ('COMPLETED', 'FAILED', 'PARTIAL'):
            break
    except Exception as e:
        pass
    time.sleep(5)
print('Done!')
