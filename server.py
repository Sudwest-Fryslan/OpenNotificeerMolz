from flask import Flask
from flask import request
from waitress import serve


import json
from datetime import datetime, timedelta
import jwt
import requests

from xml.etree import ElementTree as et
import uuid

from config import Config

app = Flask(__name__)

# debug /config on: https://flask.palletsprojects.com/en/1.1.x/errorhandling/
# https://towardsdatascience.com/deploying-flask-on-windows-b2839d8148fa

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods = ['GET', 'POST'])
def lopendezaken(path):
    if 'status' == path or '' == path:
        print("STATUS: Application is up and running (" + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3] + ")")
        return "Application is up and running", 200

    #wellicht: '/api/v1/' gebruiken als endpoint?
    #print("Request ontvangen op path:" + path)
    if 'callback/lopendezaken' != path:
        return "verkeerde path, callback/lopendezaken verwacht, maar gekregen: " + path, 400

    if request.method != "POST": 
        return "verkeerde method, POST-method verwacht", 400
    
    requestjson = json.loads(request.data)
    print("START:" + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3])
    #print("Request json:" + json.dumps(requestjson, indent=4))
    #{
    #    "kanaal": "zaken",
    #    "hoofdObject": "https://openzaak.local/zaken/api/v1/zaken/f6c29792-d84c-4940-8efb-85fe9b8776d0",
    #    "resource": "status",
    #    "resourceUrl": "https://openzaak.local/zaken/api/v1/statussen/b0d28af8-e557-4991-bda5-8b47c4a804c5",
    #    "actie": "create",
    #    "aanmaakdatum": "2022-03-15T15:42:25.590168Z",
    #    "kenmerken": {
    #        "bronorganisatie": "823288444",
    #        "zaaktype": "https://openzaak.local/catalogi/api/v1/zaaktypen/e9c19527-c47d-4ee8-9982-4ec6b61d4a8b",
    #        "vertrouwelijkheidaanduiding": "vertrouwelijk"
    #    }
    #}

    # payload die niet deugt (return met http-code 400 Bad Request)
    if not 'kanaal' in requestjson:
        print("\tAFGEBROKEN: request-json mist de key 'kanaal'")
        return "request-json mist de key 'kanaal'", 400
    if 'zaken' != requestjson['kanaal']:
        print("\tAFGEBROKEN: verkeerde kanaal, kanaal verwacht, maar gekregen:" + requestjson['kanaal'])
        return "verkeerde kanaal, kanaal verwacht, maar gekregen:" + requestjson['kanaal'], 400
    if not 'hoofdObject' in requestjson:
        print("\tAFGEBROKEN: request-json mist de key 'hoofdObject'")
        return "request-json mist de key 'hoofdObject'", 400
    if not requestjson['hoofdObject'].startswith(Config.OPENZAAK_BASEURL) :
        print("\tAFGEBROKEN: verkeerde base-url in hoofdObject, " +  Config.OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['hoofdObject'])
        return "verkeerde base-url in hoofdObject, " +  Config.OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['hoofdObject'], 400
    if not 'resource' in requestjson:
        print("\tAFGEBROKEN: request-json mist de key 'resource'")
        return "request-json mist de key 'resource'", 400
    if not 'resourceUrl' in requestjson:
        print("\tAFGEBROKEN: request-json mist de key 'resourceUrl'")
        return "request-json mist de key 'resourceUrl'", 400
    if not requestjson['resourceUrl'].startswith(Config.OPENZAAK_BASEURL) :
        print("\tAFGEBROKEN: verkeerde base-url in resourceUrl, " +  Config.OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['resourceUrl'])
        return "verkeerde base-url in resourceUrl, " +  Config.OPENZAAK_BASEURL + " verwacht, maar gekregen:" + requestjson['resourceUrl'], 400
    
    # payload waar we niets mee gaan doen (return met http-code 202 Accepted)
    # resultaat wordt ALTIJD gezet VOOR de laatste status, dus alleen bij de status updaten    
    if 'status' != requestjson['resource'] :
        print("\tNEGEREN: verkeerde resource, status verwacht, maar gekregen:" + requestjson['resource'])
        return "verkeerde resource, status verwacht, maar gekregen:" + requestjson['resource'], 202

    url = requestjson['hoofdObject']    

    payload = {
        'client_id': Config.OPENZAAK_JWT_ISSUER,
        'iat': datetime.utcnow()
    }
    encoded = jwt.encode(payload, Config.OPENZAAK_JWT_SECRET, Config.OPENZAAK_JWT_ALGORITHM)
    headers = {'Accept-Crs': 'EPSG:4326', 'Authorization': 'Bearer ' + encoded.decode('UTF-8')}
    print("\tHeaders:" + str(headers))
    # haal de zaak op
    print("\tRequesting zaak url:" + url)
    zaakresponse = requests.get(url, headers=headers)
    #print("Zaak response:" + zaakresponse)
    zaakjson = zaakresponse.json()
    #{
    #    "url": "https://openzaak.local/zaken/api/v1/zaken/14eb7888-d87f-4e03-9fbc-6f60d8e06479",
    #    "uuid": "14eb7888-d87f-4e03-9fbc-6f60d8e06479",
    #    "identificatie": "1900352191",
    #    "bronorganisatie": "823288444",
    #    "omschrijving": "Aanvraag rijbewijs 08-03-2022",
    #    "toelichting": "Aanvraag rijbewijs #1380516781",
    #    "zaaktype": "https://openzaak.local/catalogi/api/v1/zaaktypen/47029861-e38b-4c9f-a4b3-398d03aca972",
    #    "registratiedatum": "2022-03-08",
    #    "verantwoordelijkeOrganisatie": "823288444",
    #    "startdatum": "2022-03-08",
    #    "einddatum": "2022-03-15",
    #    "einddatumGepland": null,
    #    "uiterlijkeEinddatumAfdoening": "2022-06-08",
    #    "publicatiedatum": null,
    #    "communicatiekanaal": "",
    #    "productenOfDiensten": [],
    #    "vertrouwelijkheidaanduiding": "vertrouwelijk",
    #    "betalingsindicatie": "",
    #    "betalingsindicatieWeergave": "",
    #    "laatsteBetaaldatum": null,
    #    "zaakgeometrie": null,
    #    "verlenging": {
    #        "reden": "",
    #        "duur": null
    #    },
    #    "opschorting": {
    #        "indicatie": false,
    #        "reden": ""
    #    },
    #    "selectielijstklasse": "",
    #    "hoofdzaak": null,
    #    "deelzaken": [],
    #    "relevanteAndereZaken": [],
    #    "eigenschappen": [],
    #    "status": "https://openzaak.local/zaken/api/v1/statussen/5eb255d4-b9c2-4301-99a1-a7b3a792661e",
    #    "kenmerken": [],
    #    "archiefnominatie": "blijvend_bewaren",
    #    "archiefstatus": "nog_te_archiveren",
    #    "archiefactiedatum": null,
    #    "resultaat": "https://openzaak.local/zaken/api/v1/resultaten/5629dea9-855c-4717-bff0-72be83f3d3b2"
    #}    
    zaakidentificatie = zaakjson['identificatie'] 
    print('\t\tzaakidentificatie:' + zaakidentificatie)

    # haal zaaktype op
    zaaktyperesponse = requests.get(zaakjson['zaaktype'], headers=headers)
    #print("Zaaktype response:" + zaaktyperesponse.text)    
    zaaktypejson = zaaktyperesponse.json()
    #print("Zaaktype json:" + json.dumps(zaaktypejson, indent=4))    
    zaaktypeidentificatie = zaaktypejson['identificatie'] 
    print('\t\tzaaktypeidentificatie:' + zaaktypeidentificatie)

    # only supported zaaktypes
    if not zaaktypeidentificatie in Config.ACTIVE_ZAAKTYPES:
        print("\tNEGEREN: verkeerde zaaktype, active zaaktypes " +  str(Config.ACTIVE_ZAAKTYPES) + " verwacht, maar gekregen:" + zaaktypeidentificatie)
        return "verkeerde zaaktype, active zaaktypes " +  str(Config.ACTIVE_ZAAKTYPES) + " verwacht, maar gekregen:" + zaaktypeidentificatie, 202

    if Config.PRINT_ZAAKJSON:
        print("\tZaak json:" + json.dumps(zaakjson, indent=4))

    # dit gaat wel goed, laten we beginnen met het wegschrijven van de deze informatie naar de xml
    resultxml = et.parse(Config.XML_TEMPLATE)
    namespaces = {'ZKN' : 'http://www.egem.nl/StUF/sector/zkn/0310', 'StUF': 'http://www.egem.nl/StUF/StUF0301', 'BG': 'http://www.egem.nl/StUF/sector/bg/0310'}
    referentienummer = str(uuid.uuid4())
    resultxml.find('.//ZKN:stuurgegevens/StUF:referentienummer', namespaces).text = referentienummer
    resultxml.find('.//ZKN:stuurgegevens/StUF:tijdstipBericht', namespaces).text = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3] 

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
#    else:
#        root = resultxml.getroot()
#        element = resultxml.find('.//ZKN:object/ZKN:einddatum', namespaces)
#        if not element == None:
#            root.remove(element)
#        else:
#            print("ERROR: element './/ZKN:object/ZKN:einddatum' could not be found")

    # haal het resultaat op (wanneer er is)
    #if 'resultaat' in zaakjson :
    if not zaakjson['resultaat'] is None:
        resultaaturl = zaakjson['resultaat']
        print("Requesting resultaat from url:" + resultaaturl)
        resultaatresponse = requests.get(resultaaturl, headers=headers)
        print("Resultaat response:" + resultaatresponse.text)    
        resultaatjson = resultaatresponse.json()
        #print("Resultaat json:" + json.dumps(resultaatjson, indent=4))    
        resultaattoelichting = resultaatjson['toelichting'] 
        print('\t\tresultaattoelichting:' + resultaattoelichting)
    else:
        resultaattoelichting = None
        print('\tNO resultaattoelichting')

    if not resultaattoelichting == None:
        resultxml.find('.//ZKN:object/ZKN:resultaat/ZKN:omschrijving', namespaces).text = resultaattoelichting
#    else:
#        root = resultxml.getroot()
#        element = resultxml.find('.//ZKN:object/ZKN:resultaat', namespaces)
#        if not element == None:
#            root.remove(element)
#        else:
#            print("ERROR: element './/ZKN:object/ZKN:resultaat' could not be found")

    # zaaktype informatie
    resultxml.find('.//ZKN:gerelateerde/ZKN:zkt.code', namespaces).text = zaaktypeidentificatie
    resultxml.find('.//ZKN:gerelateerde/ZKN:zkt.omschrijving', namespaces).text = zaaktypejson['omschrijving'] 

    # haal de status op
    url = requestjson['resourceUrl']
    print("\tRequesting status from url:" + url)
    statusresponse = requests.get(url, headers=headers)
    #print("Status response:" + statusresponse.text)
    #print("Status json:" + json.dumps(statusjson, indent=4))    
    statusjson = statusresponse.json()
    statustoelichting = statusjson['statustoelichting'] 
    print('\t\tstatustoelichting:' + statustoelichting)

    if not resultaattoelichting == None:
        # geen resultaat ondersteuning op lopendezaken
        statustoelichting = resultaattoelichting + "(" + statustoelichting + ')'

    #resultxml.find('.//ZKN:volgnummer', namespaces).text = None
    #resultxml.find('.//ZKN:code', namespaces).text = None
    resultxml.find('.//ZKN:heeft/ZKN:gerelateerde/ZKN:omschrijving', namespaces).text = statustoelichting
    # "2021-05-13T19:06:28.580000Z", --> 20210324050209000
    resultxml.find('.//ZKN:heeft/ZKN:datumStatusGezet', namespaces).text = statusjson['datumStatusGezet'].replace('-','').replace('T','').replace(':','').replace('.','').replace('000Z','')

    # welke inwoner gaat het om?
    rollenurl = Config.OPENZAAK_BASEURL + 'zaken/api/v1/rollen'
    queryparameters = {'zaak': requestjson['hoofdObject'], 'betrokkeneType': 'natuurlijk_persoon', 'omschrijvingGeneriek' : 'initiator'}
    print("\tRequesting rollen from url:" + rollenurl)
    print("\t\tParameters:" + str(queryparameters))
    rollenresponse = requests.get(rollenurl, headers=headers, params=queryparameters)
    #print("Rollen response:" + rollenresponse.text)
    rollenjson = rollenresponse.json()
    #print("Rollen json:" + json.dumps(rollenjson, indent=4))    

    if rollenjson['count'] != 1:
        print("\tAFGEBROKEN: zaak:" + zaakidentificatie + " had niet 1 natuurlijk-persoon initiator rol (" + rollenjson['count'] + ")")
        return "zaak:" + zaakidentificatie + " had niet 1 natuurlijk-persoon initiator rol (" + rollenjson['count'] + ")", 400
    roljson = rollenjson['results'][0]
    betrokkenejson = roljson['betrokkeneIdentificatie']
    inpbsn = betrokkenejson['inpBsn'] 
    if inpbsn is None:
        print("\tAFGEBROKEN: zaak:" + zaakidentificatie + " met rol:" + roljson['omschrijving'] + " bevat geen bsn nummer")
        return "zaak:" + zaakidentificatie + " met rol:" + roljson['omschrijving'] + " bevat geen bsn nummer", 400
    print('\t\tinpbsn:' + inpbsn)
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:inp.bsn', namespaces).text = inpbsn
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geslachtsnaam', namespaces).text = betrokkenejson['geslachtsnaam'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voorvoegselGeslachtsnaam', namespaces).text = betrokkenejson['voorvoegselGeslachtsnaam'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voorletters', namespaces).text = betrokkenejson['voorletters'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:voornamen', namespaces).text = betrokkenejson['voornamen'] 
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geslachtsaanduiding', namespaces).text = betrokkenejson['geslachtsaanduiding'].upper()
    resultxml.find('.//ZKN:natuurlijkPersoon/BG:geboortedatum', namespaces).text = betrokkenejson['geboortedatum'].replace('-','')
    filename = Config.XML_OUTPUT_PATH + '/{' + referentienummer.upper() + '}.xml'
    resultxml.write(filename)
    print("\tBestand: " + filename + " weggeschreven ===")
    print("\t=== [Success] ===")
    # payload verwerkt (return met http-code 200 OK)
    return referentienummer, 200

if __name__ == '__main__':
    #app.run(host=SERVICE_HOST, port=SERVICE_PORT)
    serve(app, host=Config.SERVICE_HOST, port=Config.SERVICE_PORT, threads=1) #WAITRESS!
