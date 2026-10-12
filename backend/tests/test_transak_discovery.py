import unittest
from unittest.mock import patch
import httpx
from services.payments import transak_discovery as discovery


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_methods_quotes_fees_and_fail_closed_routes(self):
        response={"quoteId":"quote-1","fiatCurrency":"USD","cryptoCurrency":"USDC","network":"polygon",
                  "isBuyOrSell":"BUY","paymentMethod":"credit_debit_card","fiatAmount":"11.46","cryptoAmount":"10",
                  "totalFee":"1.46","conversionPrice":"1","feeBreakdown":[{"name":"Transak fee","value":"1.46"}]}
        def handler(request):
            if "fiat-currencies" in request.url.path:
                return httpx.Response(200,json={"data":{"fiatCurrencies":[{"symbol":"USD","isAllowed":True,"isSellAllowed":True,
                    "paymentOptions":[{"id":"credit_debit_card","name":"Card","minAmount":5,"maxAmount":3000,"isBuyAllowed":True,"isSellAllowed":True}]}]}})
            if "crypto-currencies" in request.url.path:
                return httpx.Response(200,json={"response":[{"symbol":"USDC","isAllowed":True,"isPayInAllowed":True,"network":{"name":"polygon","fiatCurrenciesNotSupported":[]}}]})
            return httpx.Response(200,json={"response":response})
        factory=httpx.AsyncClient
        with patch.object(discovery,"configuration",return_value=("private-key","private-secret")),patch.object(discovery.httpx,"AsyncClient",lambda **kw:factory(transport=httpx.MockTransport(handler),**kw)):
            coverage=await discovery.discover("127.0.0.1")
            self.assertNotIn("private",str(coverage))
            quote=await discovery.quote("127.0.0.1","BUY","USD","credit_debit_card","10")
            self.assertEqual(quote["totalFee"],"1.46")
            with self.assertRaises(ValueError):await discovery.quote("127.0.0.1","BUY","INR","upi","10")
            response['network']='ethereum'
            with self.assertRaises(ValueError):await discovery.quote("127.0.0.1","BUY","USD","credit_debit_card","10")
            response.update(network='polygon',isBuyOrSell='SELL',cryptoAmount='9')
            with self.assertRaises(ValueError):await discovery.quote("127.0.0.1","SELL","USD","credit_debit_card","10")
