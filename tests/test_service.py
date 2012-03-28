from suds.client import Client

from dropthesoap.service import Service, optional
from dropthesoap.schema import xs

from .helpers import DirectSudsTransport, tostring

def test_simple_service():
    service = Service('Boo', 'http://boo')

    @service.expose(returns=xs.int)
    def add(x=xs.int, y=xs.int):
        return x + y

    #open('/tmp/wow.xml', 'w').write(service.get_wsdl('http://localhost/'))

    cl = Client('some address', transport=DirectSudsTransport(service), cache=None)

    result = cl.service.add(1, 10)
    assert result == 11

def test_optional_arguments_service():
    service = Service('Boo', 'http://boo')

    @service.expose(returns=xs.int)
    def add(x=xs.int, y=optional(xs.int)):
        if y is None:
            return 1
        return 0

    cl = Client('some address', transport=DirectSudsTransport(service), cache=None)

    result = cl.service.add(1)
    assert result == 1

def test_complex_return_type():
    service = Service('Boo', 'http://boo')

    ResponseType = xs.complexType(name='ResponseType')(
        xs.sequence()(
            xs.element('foo', xs.string),
            xs.element('bar', xs.string)))

    service.schema(
        ResponseType
    )

    @service.expose(returns=ResponseType)
    def add(x=xs.int, y=xs.int):
        return ResponseType.instance(foo=x+y, bar=x-y)

    #open('/tmp/wow.xml', 'w').write(service.get_wsdl('http://localhost/'))

    cl = Client('some address', transport=DirectSudsTransport(service), cache=None)

    result = cl.service.add(1, 10)
    assert result.foo == '11'
    assert result.bar == '-9'

def test_header():
    service = Service('Boo', 'http://boo')

    service.schema(
        xs.element('AuthHeader')(xs.cts(
            xs.element('what', xs.string)))
    )


    def auth(func):
        @service.header(service.schema['AuthHeader'])
        @service.wraps(func)
        def inner(request, *args, **kwargs):
            if request.header.what == 'auth':
                return func(*args, **kwargs)
            else:
                return 'blam'

        return inner

    @auth
    @service.expose(xs.string)
    def upper(string=xs.string):
        return string.upper()

    open('/tmp/wow.xml', 'w').write(service.get_wsdl('http://localhost/'))

    cl = Client('some address', transport=DirectSudsTransport(service), cache=None)

    token = cl.factory.create('AuthHeader')
    token.what = 'auth'
    cl.set_options(soapheaders=token)
    result = cl.service.upper('boo')
    assert result == 'BOO'

    token = cl.factory.create('AuthHeader')
    token.what = 'abracadabra'
    cl.set_options(soapheaders=token)
    result = cl.service.upper('boo')
    assert result == 'blam'
