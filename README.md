# OpenNotificeerMolz

## Functionaliteit
Met deze applicatie kunnen statuswijzigingen van zaken worden gesynchronsieerd naar mijn.overheid.nl/lopendezaken.
Dat doet deze applicatie door te luisteren naar de zgw-notificaties en zal op basis van een configuratie voor bepaalde zaaktypes xml-bestanden aanmaken.
De xml-bestanden zijn in het formaat van een zakLk01 bericht, welke door mijn.overheid.nl/lopendezaken wordt ondersteund.

## Configuratie
Het notificeer bericht is informatie-arm, dit betekend dat er relatief weinig informatie wordt meegestuurd, daarom moet de applicatie aanvullende gegevens ophalen.
Daarom moet in de configuratie worden aangegeven waar de applicatie de aanvullende gegevens kan vinden en hoe daar moet worden ingelogd.
Dit kan door in het bestand config.py de volgende variabelen aan te passen:
    OPENZAAK_BASEURL = 'https://openzaak.local'
    OPENZAAK_JWT_ISSUER = 'test'
    OPENZAAK_JWT_SECRET = 'test'

Daarnaast moet er bekend zijn voor welke zaaktypes er gesyncroniseerd moet worden, dit kan met de variabele:
    ACTIVE_ZAAKTYPES = {'B1026'}

## Running on Windows
To get the application running on Windows, this application uses waitress as the WSGI server.
Server can be started by running >python server.py