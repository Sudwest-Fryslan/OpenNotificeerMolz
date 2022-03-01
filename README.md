# OpenNotificeerMolz

## Wat doet het?
Met deze applicatie kunnen statuswijzigingen van zaken worden gesynchronsieerd naar mijn.overheid.nl/lopendezaken.

Dit doet deze applicatie door te luisteren naar de zgw-notificaties en zal op basis van een configuratie voor bepaalde zaaktypes xml-bestanden aanmaken. De xml-bestanden zijn in het formaat van een zakLk01 bericht, welke door mijn.overheid.nl/lopendezaken wordt ondersteund.

## Hoe stel ik het in?
Het notificeer bericht is informatie-arm, dit betekend dat er relatief weinig informatie wordt meegestuurd, daarom moet de applicatie aanvullende gegevens ophalen. Daarom moet in de configuratie worden aangegeven waar de applicatie de aanvullende gegevens kan vinden en hoe daar moet worden ingelogd.

Instellen kan door in het bestand config.py de volgende variabelen aan te passen:

```
	...
	OPENZAAK_BASEURL = 'https://openzaak.local'
    	OPENZAAK_JWT_ISSUER = 'test'
	OPENZAAK_JWT_SECRET = 'test'
	...
```

Om in te stellen welke zaaktypes er gesynchroniseerd moeten worden, kunnen de volgende variable worden aangepast: 

```
	...
	ACTIVE_ZAAKTYPES = {'B1026', 'ANDER-ZAAKTYPE-IDENTIFICATIE'}
	...
```
## Hoe zien de berichten eruit?
Er wordt verwacht dat de notificaties als POST binnenkomen op http://localhost/callback/lopendezaken 
```
POST /api/v1/notificaties HTTP/1.0

Authorization: Bearer abcdef1234
Content-Type: application/json

{
    "kanaal": "zaken",
    "hoofdObject": "https://zaken-api.vng.cloud/api/v1/zaken/d7a22",
    "resource": "status",
    "resourceUrl": "https://zaken-api.vng.cloud/api/v1/statussen/d7a22/721c9",
    "actie": "create",
    "aanmaakdatum": "2018-01-01T17:00:00Z",
    "kenmerken": {
        "bron": "082096752011",
        "zaaktype": "https://example.com/api/v1/zaaktypen/5aa5c",
        "vertrouwelijkeidaanduiding": "openbaar"
    }
}
```
(https://vng-realisatie.github.io/gemma-zaken/themas/achtergronddocumentatie/notificaties)

## Hoe draai ik het onder windows?
De eerste keer, of bij een update, moeten de modules van python allemaal geinstalleerd/geupdate worden, dit kan met het volgende commando:

```
D:\git\OpenNotificeerMolz>pip install -r requirements.txt
```

Om daarna de applicatie te draaien vanaf de commandprompt onder Window moet het volgende commando worden gegeven. 

```
D:\git\OpenNotificeerMolz>python server.py
```

Omdat deze applicatie onder Windows moet draaien gebruikt deze applcatie de waitress-WSGI server.
--

###### Voor de vulling van de gegevens in de zaakregistratie component, wordt een data-structuur verwacht die gelijk is aan het gebruikt bij de https://github.com/Sudwest-Fryslan/OpenZaakBrug 
