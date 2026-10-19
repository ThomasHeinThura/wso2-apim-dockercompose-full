#!/usr/bin/env python3
"""Create, publish, invoke, and delete a temporary unauthenticated API."""
import base64, json, pathlib, subprocess, time, urllib.parse, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
env=dict(line.split('=',1) for line in (ROOT/'.env').read_text().splitlines() if line and not line.startswith('#'))
def request(host,path,method='GET',data=None,headers=None,form=None):
    args=['curl','--noproxy','*','--silent','--show-error','--max-time','60',
          '--cacert',str(ROOT/'certs/bimats.crt'),'--resolve',f'{host}:443:127.0.0.1',
          '--request',method,'--write-out','\n%{http_code}',f'https://{host}{path}']
    for k,v in (headers or {}).items(): args+=['--header',f'{k}: {v}']
    payload=None
    if data is not None:
        args+=['--header','Content-Type: application/json','--data-binary','@-'];payload=json.dumps(data)
    if form is not None:
        args+=['--header','Content-Type: application/x-www-form-urlencoded','--data-binary','@-'];payload=urllib.parse.urlencode(form)
    r=subprocess.run(args,input=payload,capture_output=True,text=True,check=True)
    body,status=r.stdout.rsplit('\n',1)
    try: body=json.loads(body)
    except ValueError: pass
    return int(status),body
admin='Basic '+base64.b64encode(('admin:'+env['APIM_ADMIN_PASSWORD']).encode()).decode()
status,client=request('apim.example.com','/client-registration/v0.17/register','POST',
    {'callbackUrl':'https://apim.example.com','clientName':'bimats-smoke-'+uuid.uuid4().hex[:8],
     'owner':'admin','grantType':'password client_credentials','saasApp':True}, {'Authorization':admin})
assert status in (200,201), ('DCR',status,client)
basic='Basic '+base64.b64encode((client['clientId']+':'+client['clientSecret']).encode()).decode()
api_id=None
try:
    status,token=request('apim.example.com','/oauth2/token','POST',headers={'Authorization':basic},
        form={'grant_type':'password','username':'admin','password':env['APIM_ADMIN_PASSWORD'],
              'scope':'apim:api_view apim:api_create apim:api_publish apim:api_delete'})
    assert status==200, ('token',status,token)
    auth={'Authorization':'Bearer '+token['access_token']}
    suffix=uuid.uuid4().hex[:8]
    context='/bimats-smoke-'+suffix
    status,api=request('apim.example.com','/api/am/publisher/v4/apis','POST',{
        'name':'BimatsSmoke'+suffix,'context':context,'version':'1.0.0','isDefaultVersion':True,
        'type':'HTTP','transport':['https'],'policies':['Unlimited'],
        'endpointConfig':{'endpoint_type':'http','production_endpoints':{'url':'http://localhost:9763/services'}},
        'operations':[{'target':'/Version','verb':'GET','authType':'None','throttlingPolicy':'Unlimited'}]},auth)
    assert status==201, ('create API',status,api)
    api_id=api['id']
    print('PASS create temporary API through CP')
    status,result=request('apim.example.com',f'/api/am/publisher/v4/apis/{api_id}/revisions','POST',{'description':'Local routing verification'},auth)
    assert status==201, ('revision',status,result)
    revision=result['id']
    status,result=request('apim.example.com',f'/api/am/publisher/v4/apis/{api_id}/deploy-revision?revisionId={revision}',
        'POST',[{'name':'Default','vhost':'api.example.com','displayOnDevportal':True}],auth)
    assert status in (200,201), ('deploy',status,result)
    status,result=request('apim.example.com',f'/api/am/publisher/v4/apis/change-lifecycle?action=Publish&apiId={api_id}','POST',headers=auth)
    assert status==200, ('publish',status,result)
    print('PASS publish and deploy API to Default gateway')
    for attempt in range(15):
        status,body=request('api.example.com',context+'/1.0.0/Version')
        if status==200: break
        time.sleep(2)
    assert status==200 and '4.7.0' in str(body), ('gateway invoke',status,body)
    print('PASS invoke https://api.example.com'+context+'/1.0.0/Version: HTTP 200, WSO2 API Manager 4.7.0')
finally:
    if api_id:
        status,body=request('apim.example.com',f'/api/am/publisher/v4/apis/{api_id}','DELETE',headers=auth)
        if status not in (200,202,204):
            print('Cleanup API returned HTTP',status,body)
        else: print('PASS delete temporary API')
    # Remove the temporary OAuth client using authenticated DCR.
    status,_=request('apim.example.com','/api/identity/oauth2/dcr/v1.1/register/'+urllib.parse.quote(client['clientId']),'DELETE',headers={'Authorization':admin})
    assert status in (200,204), ('OAuth client cleanup',status)
    print('PASS delete temporary OAuth client')
