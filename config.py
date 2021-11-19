class Config(object):
    XML_TEMPLATE = 'template.xml'
    XML_OUTPUT_PATH = '.'

    SERVICE_HOST = '0.0.0.0'
    SERVICE_PORT = 80

    ACTIVE_ZAAKTYPES = {'B1026'}

    OPENZAAK_BASEURL = 'https://openzaak.local'
    OPENZAAK_JWT_ISSUER = 'test'
    OPENZAAK_JWT_SECRET = 'test'
    OPENZAAK_JWT_ALGORITHM = 'HS256'


