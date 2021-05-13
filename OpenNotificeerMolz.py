from flask import Flask
from flask import request

import json
from datetime import datetime, timedelta
import jwt
import requests

from xml.etree import ElementTree as et
import uuid

app = Flask(__name__)

XML_TEMPLATE = 'template.xml'
XML_OUTPUT_PATH = '.'

SERVICE_HOST = '0.0.0.0'
SERVICE_PORT = 80

ACTIVE_ZAAKTYPES = {'B1026'}

OPENZAAK_BASEURL = 'https://openzaak.local'
OPENZAAK_JWT_ISSUER = 'test'
OPENZAAK_JWT_SECRET = 'test'
OPENZAAK_JWT_ALGORITHM = 'HS256'

#debug /config on: https://flask.palletsprojects.com/en/1.1.x/errorhandling/

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods = ['GET', 'POST'])
def lopendezaken(path):
    #print("Request ontvangen op path:" + path)
    if 'callback/lopendezaken' != path:
        return "verkeerde path, callback/lopendezaken verwacht, maar gekregen: " + path, 400

    requestjson = json.loads(request.data)
    #print("Ontvangen json:" + json.dumps(requestjson, indent=4))

    if 'zaken' != requestjson['kanaal']:
        return "verkeerde kanaal, kanaal verwacht, maar gekregen:" + requestjson['kanaal'], 400

    if 'status' != requestjson['resource']:
        return "verkeerde resource, status verwacht, maar gekregen:" + requestjson['resource'], 400

    if not requestjson['hoofdObject'].startswith(OPENZAAK_BASEURL) :
        return "verkeerde base-url in hoofdObject, " +  OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['hoofdObject'], 400

    if not requestjson['resourceUrl'].startswith(OPENZAAK_BASEURL) :
        return "verkeerde base-url in resourceUrl, " +  OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['resourceUrl'], 400

    payload = {
        'client_id': OPENZAAK_JWT_ISSUER,
        'iat': datetime.utcnow()
    }
    jwt_token = jwt.encode(payload, OPENZAAK_JWT_SECRET, OPENZAAK_JWT_ALGORITHM)
    headers = {'Accept-Crs': 'EPSG:4326', 'Authorization': 'Bearer ' + jwt_token}
    # haal de zaak op
    zaakjson = requests.get(requestjson['hoofdObject'], headers=headers).json()
    #print("Zaak json:" + json.dumps(zaakjson, indent=4))    
    zaakidentificatie = zaakjson['identificatie'] 
    print('>> zaakidentificatie:' + zaakidentificatie)

    # haal zaaktype op
    zaaktypejson = requests.get(zaakjson['zaaktype'], headers=headers).json()
    #print("Zaaktype json:" + json.dumps(zaaktypejson, indent=4))    
    zaaktypeidentificatie = zaaktypejson['identificatie'] 
    print('>> zaaktypeidentificatie:' + zaaktypeidentificatie)

    # only supported zaaktypes
    if not zaaktypeidentificatie in ACTIVE_ZAAKTYPES:
        return "verkeerde zaaktype, active zaaktypes " +  str(ACTIVE_ZAAKTYPES) + " verwacht, maar gekregen:" + zaaktypeidentificatie, 400

    # dit gaat wel goed, laten we beginnen met het wegschrijven van de deze informatie naar de xml
    resultxml = et.parse(XML_TEMPLATE)
    namespaces = {'ZKN' : 'http://www.egem.nl/StUF/sector/zkn/0310', 'StUF': 'http://www.egem.nl/StUF/StUF0301', 'BG': 'http://www.egem.nl/StUF/sector/bg/0310'}
    referentienummer = str(uuid.uuid4())
    resultxml.find('.//ZKN:stuurgegevens/StUF:referentienummer', namespaces).text = referentienummer
    resultxml.find('.//ZKN:stuurgegevens/StUF:tijdstipBericht', namespaces).text = datetime.utcnow().strftime('%Y%d%d%H%M%S%f') 

    # zaak informatie
    resultxml.find('.//ZKN:object', namespaces).attrib[et.QName(namespaces['StUF'], 'sleutelVerzendend')] = zaakidentificatie
    resultxml.find('.//ZKN:object/ZKN:identificatie', namespaces).text = zaakidentificatie
    resultxml.find('.//ZKN:object/ZKN:omschrijving', namespaces).text = zaakjson['omschrijving']
    resultxml.find('.//ZKN:object/ZKN:toelichting', namespaces).text = zaakjson['toelichting']
    resultxml.find('.//ZKN:object/ZKN:startdatum', namespaces).text = zaakjson['startdatum'].replace('-','')

    #einddatum?
    if not zaakjson['einddatum'] is None:
        einddatumelement = resultxml.find('.//ZKN:object/ZKN:einddatum', namespaces)
        einddatumelement.attrib.clear()
        einddatumelement.text = zaakjson['einddatum'].replace('-','')

    # zaaktype informatie
    resultxml.find('.//ZKN:gerelateerde/ZKN:zkt.code', namespaces).text = zaaktypeidentificatie
    resultxml.find('.//ZKN:gerelateerde/ZKN:zkt.omschrijving', namespaces).text = zaaktypejson['omschrijving'] 

    # haal de status op
    statusjson = requests.get(requestjson['resourceUrl'], headers=headers).json()
    #print("Status json:" + json.dumps(statusjson, indent=4))    
    statustoelichting = statusjson['statustoelichting'] 
    print('>> statustoelichting:' + statustoelichting)

    # haal het resultaat op (wanneer er is)
    if not zaakjson['resultaat'] is None :
        resultaatjson = requests.get(zaakjson['resultaat'], headers=headers).json()
        #print("Resultaat json:" + json.dumps(resultaatjson, indent=4))    
        resultaattoelichting = resultaatjson['toelichting'] 
        print('>> resultaattoelichting:' + resultaattoelichting)
    else:
        resultaattoelichting = None
        print('>> NO resultaattoelichting:' + resultaattoelichting)

    if not resultaattoelichting == None:
        # geen resultaat ondersteuning op lopendezaken
        statustoelichting = resultaattoelichting + "(" + statustoelichting + ')'

    #resultxml.find('.//ZKN:volgnummer', namespaces).text = None
    #resultxml.find('.//ZKN:code', namespaces).text = None
    resultxml.find('.//ZKN:heeft/ZKN:gerelateerde/ZKN:omschrijving', namespaces).text = statustoelichting
    # "2021-05-13T19:06:28.580000Z", --> 20210324050209000
    resultxml.find('.//ZKN:heeft/ZKN:datumStatusGezet', namespaces).text = statusjson['datumStatusGezet'].replace('-','').replace('T','').replace(':','').replace('.','').replace('000Z','')

    # welke inwoner gaat het om?
    rollenurl = OPENZAAK_BASEURL + '/zaken/api/v1/rollen'    
    queryparameters = {'zaak': requestjson['hoofdObject'], 'betrokkeneType': 'natuurlijk_persoon', 'omschrijvingGeneriek' : 'initiator'}
    rollenjson = requests.get(rollenurl, headers=headers, params=queryparameters).json()
    #print("Rollen json:" + json.dumps(rollenjson, indent=4))    
    if rollenjson['count'] != 1:
        return "zaak:" + zaakidentificatie + " had niet 1 natuurlijk-persoon initiator rol (" + rollenjson['count'] + ")", 400
    roljson = rollenjson['results'][0]
    betrokkenejson = roljson['betrokkeneIdentificatie']
    inpbsn = betrokkenejson['inpBsn'] 
    if inpbsn is None:
        return "zaak:" + zaakidentificatie + " met rol:" + roljson['omschrijving'] + " bevat geen bsn nummer", 400
    print('>> inpbsn:' + inpbsn)
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:inp.bsn', namespaces).text = inpbsn
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geslachtsnaam', namespaces).text = betrokkenejson['geslachtsnaam'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voorvoegselGeslachtsnaam', namespaces).text = betrokkenejson['voorvoegselGeslachtsnaam'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voorletters', namespaces).text = betrokkenejson['voorletters'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voornamen', namespaces).text = betrokkenejson['voornamen'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geslachtsaanduiding', namespaces).text = betrokkenejson['geslachtsaanduiding'].upper()
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geboortedatum', namespaces).text = betrokkenejson['geboortedatum'].replace('-','')

    resultxml.write('{' + referentienummer.upper() + '}.xml')
    
    return referentienummer

if __name__ == '__main__':
    app.run(host=SERVICE_HOST, port=SERVICE_PORT)