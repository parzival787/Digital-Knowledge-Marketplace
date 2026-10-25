import asyncio
import json
import unittest
from unittest.mock import patch
from services.payments import payouts
from tests import test_transak


class PayoutTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = test_transak.TransakTests.asyncSetUp
    asyncTearDown = test_transak.TransakTests.asyncTearDown

    async def prepare(self):
        mock = patch.object(payouts, 'get_conn', self.isolated)
        mock.start(); self.addCleanup(mock.stop)
        await payouts.setup_payouts()
        await payouts.create_payout({'id':1, 'wallet_address':'0x'+'1'*40}, '127.0.0.1', 'EUR')
        conn = await self.isolated()
        self.payout = await conn.fetchrow('SELECT * FROM seller_payouts')
        await conn.close()
        self.order.update(isBuyOrSell='SELL', fiatCurrency='EUR', cryptoAmount='100',
            partnerOrderId=str(self.payout['id']), partnerCustomerId=str(self.payout['customer_reference']),
            walletAddress='PROVIDER_DESTINATION_NOT_SELLER')

    async def refresh(self, user=1):
        return await payouts.refresh_payout(self.payout['id'], self.order_id, user)

    async def test_binding_duplicates_and_safe_fields(self):
        await self.prepare()
        with self.assertRaises(ValueError): await self.refresh(2)
        customer = self.order['partnerCustomerId']
        self.order['partnerCustomerId'] = 'wrong'
        with self.assertRaises(ValueError): await self.refresh()
        self.order['partnerCustomerId'] = customer
        self.order['status'] = 'COMPLETED'
        results = await asyncio.gather(self.refresh(), self.refresh())
        self.assertTrue(all(r['state']=='verified' for r in results))
        self.assertFalse(results[0]['grants_access'])
        self.assertNotIn('email', str(results))
        conn = await self.isolated()
        self.assertEqual(await conn.fetchval('SELECT count(*) FROM payout_observations'), 1)
        await conn.close()
        self.assertEqual((await payouts.history({'id':2}))['payouts'], [])

    async def test_changed_amount_resolution_and_currency_cannot_be_overridden(self):
        await self.prepare()
        self.order['status'] = 'COMPLETED'
        await self.refresh()
        self.order['fiatAmount'] = 99
        result = await self.refresh()
        self.assertEqual(result['state'], 'review_required')
        self.assertEqual(result['receipt']['fiat_amount'], '100')
        conn = await self.isolated()
        observed = json.loads(await conn.fetchval('SELECT observed FROM seller_payouts'))
        with self.assertRaises(ValueError):
            await payouts.resolve_payout(self.payout['id'], 'stale', 'Checked provider evidence')
        await payouts.resolve_payout(self.payout['id'], payouts.digest(observed), 'Checked provider evidence')
        self.assertEqual(await conn.fetchval('SELECT count(*) FROM payout_resolutions'), 1)
        self.order['fiatCurrency'] = 'USD'
        self.assertEqual((await self.refresh())['state'], 'review_required')
        observed = json.loads(await conn.fetchval('SELECT observed FROM seller_payouts'))
        with self.assertRaises(ValueError):
            await payouts.resolve_payout(self.payout['id'], payouts.digest(observed), 'Cannot accept wrong currency')
        await conn.close()

    async def test_terminal_regression_late_completion_and_restart_outage(self):
        await self.prepare()
        self.order['status'] = 'FAILED'
        await self.refresh()
        self.order['status'] = 'COMPLETED'
        self.assertEqual((await self.refresh())['state'], 'review_required')
        conn = await self.isolated()
        observed = json.loads(await conn.fetchval('SELECT observed FROM seller_payouts'))
        await payouts.resolve_payout(self.payout['id'], payouts.digest(observed), 'Late payout verified externally')
        self.order['status'] = 'PROCESSING'
        self.assertEqual((await self.refresh())['state'], 'review_required')
        self.order['status'] = 'COMPLETED'
        await self.refresh()
        observed = json.loads(await conn.fetchval('SELECT observed FROM seller_payouts'))
        await payouts.resolve_payout(self.payout['id'], payouts.digest(observed), 'Latest completed evidence checked')
        self.fail = True
        await asyncio.gather(payouts.reconcile_payouts(), payouts.reconcile_payouts())
        row = await conn.fetchrow('SELECT * FROM seller_payouts')
        self.assertEqual(json.loads(row['receipt'])['status'], 'COMPLETED')
        self.assertIn('unavailable', row['error'])
        self.assertNotIn('secret', row['error'])
        self.fail = False
        await conn.execute('UPDATE seller_payouts SET next_check_at=NOW()')
        await payouts.setup_payouts()
        await payouts.reconcile_payouts()
        self.assertIsNone(await conn.fetchval('SELECT error FROM seller_payouts'))
        await conn.close()
