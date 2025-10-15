from spyne import Application, ServiceBase, Unicode, Double, Iterable, ComplexModel, rpc
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import os

# Define a complex type for rates response
class Rate(ComplexModel):
    currency = Unicode
    rate = Double

class CurrencyService(ServiceBase):
    fallback_rates = {
        'USD': 1.0,
        'EUR': 0.85,
        'GBP': 0.75,
        'JPY': 110.0
    }
    supported_currencies = list(fallback_rates.keys())  # Class-level attributes

    def __init__(self):
        super().__init__()

    @rpc(Unicode, Unicode, Double, _returns=Double)
    def convert_currency(ctx, from_currency, to_currency, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if from_currency not in CurrencyService.supported_currencies or to_currency not in CurrencyService.supported_currencies:
            raise ValueError("Invalid currency")
        rate = CurrencyService.fallback_rates[to_currency] / CurrencyService.fallback_rates[from_currency]
        return amount * rate

    @rpc(Unicode, _returns=Iterable(Rate))
    def get_rates(ctx, base_currency):
        if base_currency not in CurrencyService.supported_currencies:
            raise ValueError("Invalid base currency")
        base_rate = CurrencyService.fallback_rates[base_currency]
        for currency, rate in CurrencyService.fallback_rates.items():
            if currency != base_currency:
                yield Rate(currency=currency, rate=rate / base_rate)

app = Application([CurrencyService], tns='currency.soap',
                  in_protocol=Soap11(validator='lxml'),
                  out_protocol=Soap11())

# Custom WSGI wrapper to serve WSDL on GET ?wsdl
def application(environ, start_response):
    if environ.get('REQUEST_METHOD') == 'GET' and  environ.get('QUERY_STRING', '') == 'wsdl':
        # Generate WSDL (use full URL base for portability)
        base_url = f"http://{environ.get('HTTP_HOST', 'localhost:8000')}?wsdl"
        wsdl_content = app.wsdl11.build_interface_document(base_url)
        wsdl_bytes = wsdl_content.encode('utf-8')
        start_response('200 OK', [
            ('Content-Type', 'text/xml; charset=utf-8'),
            ('Content-Length', str(len(wsdl_bytes)))
        ])
        return [wsdl_bytes]
    else:
        # Delegate to Spyne for SOAP POST
        return WsgiApplication(app)(environ, start_response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = make_server("0.0.0.0", port, application)
    print(f"SOAP server running on port {port}")
    server.serve_forever()
