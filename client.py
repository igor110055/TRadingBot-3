import time
import urllib.parse
from typing import Optional, Dict, Any, List

from requests import Request, Session, Response
import hmac
from ciso8601 import parse_datetime



class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def get_all_futures(self) -> List[dict]:
        return self._get('futures')

    def get_future(self, future_name: str = None) -> dict:
        return self._get(f'futures/{future_name}')

    def get_markets(self) -> List[dict]:
        return self._get('markets')

    def get_orderbook(self, market: str, depth: int = None) -> dict:
        return self._get(f'markets/{market}/orderbook', {'depth': depth})

    def get_trades(self, market: str, start_time: float = None, end_time: float = None) -> dict:
        return self._get(f'markets/{market}/trades', {'start_time': start_time, 'end_time': end_time})

    def get_account_info(self) -> dict:
        return self._get(f'account')

    def get_open_orders(self, market: str = None) -> List[dict]:
        return self._get(f'orders', {'market': market})

    def get_order_history(
        self, market: str = None, side: str = None, order_type: str = None,
        start_time: float = None, end_time: float = None
    ) -> List[dict]:
        return self._get(f'orders/history', {
            'market': market,
            'side': side,
            'orderType': order_type,
            'start_time': start_time,
            'end_time': end_time
        })

    def get_conditional_order_history(
        self, market: str = None, side: str = None, type: str = None,
        order_type: str = None, start_time: float = None, end_time: float = None
    ) -> List[dict]:
        return self._get(f'conditional_orders/history', {
            'market': market,
            'side': side,
            'type': type,
            'orderType': order_type,
            'start_time': start_time,
            'end_time': end_time
        })

    def modify_order(
        self, existing_order_id: Optional[str] = None,
        existing_client_order_id: Optional[str] = None, price: Optional[float] = None,
        size: Optional[float] = None, client_order_id: Optional[str] = None,
    ) -> dict:
        assert (existing_order_id is None) ^ (existing_client_order_id is None), \
            'Must supply exactly one ID for the order to modify'
        assert (price is None) or (size is None), 'Must modify price or size of order'
        path = f'orders/{existing_order_id}/modify' if existing_order_id is not None else \
            f'orders/by_client_id/{existing_client_order_id}/modify'
        return self._post(path, {
            **({'size': size} if size is not None else {}),
            **({'price': price} if price is not None else {}),
            ** ({'clientId': client_order_id} if client_order_id is not None else {}),
        })

    def get_conditional_orders(self, market: str = None) -> List[dict]:
        return self._get(f'conditional_orders', {'market': market})

    def place_order(self, market: str, side: str, price: float, size: float, type: str = 'limit',
                    reduce_only: bool = False, ioc: bool = False, post_only: bool = False,
                    client_id: str = None, reject_after_ts: float = None) -> dict:
        return self._post('orders', {
            'market': market,
            'side': side,
            'price': price,
            'size': size,
            'type': type,
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only,
            'clientId': client_id,
            'rejectAfterTs': reject_after_ts
        })

    def place_conditional_order(
        self, market: str, side: str, size: float, type: str = 'stop',
        limit_price: float = None, reduce_only: bool = False, cancel: bool = True,
        trigger_price: float = None, trail_value: float = None
    ) -> dict:
        """
        To send a Stop Market order, set type='stop' and supply a trigger_price
        To send a Stop Limit order, also supply a limit_price
        To send a Take Profit Market order, set type='trailing_stop' and supply a trigger_price
        To send a Trailing Stop order, set type='trailing_stop' and supply a trail_value
        """
        assert type in ('stop', 'take_profit', 'trailing_stop')
        assert type not in ('stop', 'take_profit') or trigger_price is not None, \
            'Need trigger prices for stop losses and take profits'
        assert type not in ('trailing_stop',) or (trigger_price is None and trail_value is not None), \
            'Trailing stops need a trail value and cannot take a trigger price'

        return self._post('conditional_orders', {
            'market': market,
            'side': side,
            'triggerPrice': trigger_price,
            'size': size,
            'reduceOnly': reduce_only,
            'type': 'stop',
            'cancelLimitOnTrigger': cancel,
            'orderPrice': limit_price
        })

    def cancel_order(self, order_id: str) -> dict:
        return self._delete(f'orders/{order_id}')

    def cancel_orders(
        self, market_name: str = None,
        conditional_orders: bool = False, limit_orders: bool = False
    ) -> dict:
        return self._delete(f'orders', {
            'market': market_name,
            'conditionalOrdersOnly': conditional_orders,
            'limitOrdersOnly': limit_orders
        })

    def get_fills(self, market: str = None, start_time: float = None,
        end_time: float = None, min_id: int = None, order_id: int = None
    ) -> List[dict]:
        return self._get('fills', {
            'market': market,
            'start_time': start_time,
            'end_time': end_time,
            'minId': min_id,
            'orderId': order_id
        })

    def get_balances(self) -> List[dict]:
        return self._get('wallet/balances')

    def get_total_usd_balance(self) -> int:
        total_usd = 0
        balances = self._get('wallet/balances')
        for balance in balances:
            total_usd += balance['usdValue']
        return total_usd

    def get_all_balances(self) -> List[dict]:
        return self._get('wallet/all_balances')

    def get_total_account_usd_balance(self) -> int:
        total_usd = 0
        all_balances = self._get('wallet/all_balances')
        for wallet in all_balances:
            for balance in all_balances[wallet]:
                total_usd += balance['usdValue']
        return total_usd

    def get_positions(self, show_avg_price: bool = False) -> List[dict]:
        return self._get('positions', {'showAvgPrice': show_avg_price})

    def get_position(self, name: str, show_avg_price: bool = False) -> dict:
        return next(filter(lambda x: x['future'] == name, self.get_positions(show_avg_price)), None)

    def get_all_trades(self, market: str, start_time: float = None, end_time: float = None) -> List:
        ids = set()
        limit = 100
        results = []
        while True:
            response = self._get(f'markets/{market}/trades', {
                'end_time': end_time,
                'start_time': start_time,
            })
            deduped_trades = [r for r in response if r['id'] not in ids]
            results.extend(deduped_trades)
            ids |= {r['id'] for r in deduped_trades}
            print(f'Adding {len(response)} trades with end time {end_time}')
            if len(response) == 0:
                break
            end_time = min(parse_datetime(t['time']) for t in response).timestamp()
            if len(response) < limit:
                break
        return results

    def get_historical_prices(
        self, market: str, resolution: int = 300, start_time: float = None,
        end_time: float = None
    ) -> List[dict]:
        return self._get(f'markets/{market}/candles', {
            'resolution': resolution,
            'start_time': start_time,
            'end_time': end_time
        })

    def get_last_historical_prices(self, market: str, resolution: int = 300) -> List[dict]:
        return self._get(f'markets/{market}/candles/last', {'resolution': resolution})

    def get_borrow_rates(self) -> List[dict]:
        return self._get('spot_margin/borrow_rates')

    def get_borrow_history(self, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('spot_margin/borrow_history', {'start_time': start_time, 'end_time': end_time})

    def get_lending_history(self, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('spot_margin/lending_history', {
            'start_time': start_time,
            'end_time': end_time
        })

    def get_expired_futures(self) -> List[dict]:
        return self._get('expired_futures')

    def get_coins(self) -> List[dict]:
        return self._get('wallet/coins')

    def get_future_stats(self, future_name: str) -> dict:
        return self._get(f'futures/{future_name}/stats')

    def get_single_market(self, market: str = None) -> Dict:
        return self._get(f'markets/{market}')

    def get_market_info(self, market: str = None) -> dict:
        return self._get('spot_margin/market_info', {'market': market})

    def get_trigger_order_triggers(self, conditional_order_id: str = None) -> List[dict]:
        return self._get(f'conditional_orders/{conditional_order_id}/triggers')

    def get_trigger_order_history(self, market: str = None) -> List[dict]:
        return self._get('conditional_orders/history', {'market': market})

    def get_staking_balances(self) -> List[dict]:
        return self._get('staking/balances')

    def get_stakes(self) -> List[dict]:
        return self._get('staking/stakes')

    def get_staking_rewards(self, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('staking/staking_rewards', {
            'start_time': start_time,
            'end_time': end_time
        })

    def place_staking_request(self, coin: str = 'SRM', size: float = None) -> dict:
        return self._post('srm_stakes/stakes',)

    def get_funding_rates(self, future: str = None, start_time: float = None, end_time: float = None)-> List[dict]:
        return self._get('funding_rates', {
            'future': future,
            'start_time': start_time,
            'end_time': end_time
        })

    def get_all_funding_rates(self) -> List[dict]:
        return self._get('funding_rates')

    def get_funding_payments(self, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('funding_payments', {
            'start_time': start_time,
            'end_time': end_time
        })

    def create_subaccount(self, nickname: str) -> dict:
        return self._post('subaccounts', {'nickname': nickname})

    def get_subaccount_balances(self, nickname: str) -> List[dict]:
        return self._get(f'subaccounts/{nickname}/balances')

    def get_deposit_address(self, ticker: str) -> dict:
        return self._get(f'wallet/deposit_address/{ticker}')

    def get_deposit_history(self) -> List[dict]:
        return self._get('wallet/deposits')

    def get_withdrawal_fee(self, coin: str, size: int, address: str, method: str = None, tag: str = None) -> Dict:
        return self._get('wallet/withdrawal_fee', {
            'coin': coin,
            'size': size,
            'address': address,
            'method': method,
            'tag': tag
        })

    def get_withdrawals(self, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('wallet/withdrawals', {'start_time': start_time, 'end_time': end_time})

    def get_saved_addresses(self, coin: str = None) -> dict:
        return self._get('wallet/saved_addresses', {'coin': coin})

    def submit_fiat_withdrawal(self, coin: str, size: int, saved_address_id: int, code: int = None) -> Dict:
        return self._post('wallet/fiat_withdrawals', {
        'coin': coin,
        'size': size,
        'savedAddressId': saved_address_id,
        'code': code
    })

    def get_latency_stats(self, days: int = 1, subaccount_nickname: str = None) -> Dict:
        return self._get('stats/latency_stats', {'days': days, 'subaccount_nickname': subaccount_nickname})
import json
import time
import zlib
from collections import defaultdict, deque
from itertools import zip_longest
from typing import DefaultDict, Deque, List, Dict, Tuple, Optional
from gevent.event import Event

from websocket_manager import WebsocketManager


class FtxWebsocketClient(WebsocketManager):
    _ENDPOINT = 'wss://ftx.com/ws/'

    def __init__(self) -> None:
        super().__init__()
        self._trades: DefaultDict[str, Deque] = defaultdict(lambda: deque([], maxlen=10000))
        self._fills: Deque = deque([], maxlen=10000)
        self._api_key = '7SmkF9PmOfxUF-yphj9XYJqYxp-5DJLm19u0CPqt'  # TODO: Place your API key here
        self._api_secret = 'y9Sd3yhKKz9F69hOAW0cKh9umAYVHsGguoMfOIHA'  # TODO: Place your API secret here
        self._orderbook_update_events: DefaultDict[str, Event] = defaultdict(Event)
        self._reset_data()

    def _on_open(self, ws):
        self._reset_data()

    def _reset_data(self) -> None:
        self._subscriptions: List[Dict] = []
        self._orders: DefaultDict[int, Dict] = defaultdict(dict)
        self._tickers: DefaultDict[str, Dict] = defaultdict(dict)
        self._orderbook_timestamps: DefaultDict[str, float] = defaultdict(float)
        self._orderbook_update_events.clear()
        self._orderbooks: DefaultDict[str, Dict[str, DefaultDict[float, float]]] = defaultdict(
            lambda: {side: defaultdict(float) for side in {'bids', 'asks'}})
        self._orderbook_timestamps.clear()
        self._logged_in = False
        self._last_received_orderbook_data_at: float = 0.0

    def _reset_orderbook(self, market: str) -> None:
        if market in self._orderbooks:
            del self._orderbooks[market]
        if market in self._orderbook_timestamps:
            del self._orderbook_timestamps[market]

    def _get_url(self) -> str:
        return self._ENDPOINT

    def _login(self) -> None:
        ts = int(time.time() * 1000)
        self.send_json({'op': 'login', 'args': {
            'key': self._api_key,
            'sign': hmac.new(
                self._api_secret.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
            'time': ts,
        }})
        self._logged_in = True

    def _subscribe(self, subscription: Dict) -> None:
        self.send_json({'op': 'subscribe', **subscription})
        self._subscriptions.append(subscription)

    def _unsubscribe(self, subscription: Dict) -> None:
        self.send_json({'op': 'unsubscribe', **subscription})
        while subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

    def get_fills(self) -> List[Dict]:
        if not self._logged_in:
            self._login()
        subscription = {'channel': 'fills'}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        return list(self._fills.copy())

    def get_orders(self) -> Dict[int, Dict]:
        if not self._logged_in:
            self._login()
        subscription = {'channel': 'orders'}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        return dict(self._orders.copy())

    def get_trades(self, market: str) -> List[Dict]:
        subscription = {'channel': 'trades', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        return list(self._trades[market].copy())

    def get_orderbook(self, market: str) -> Dict[str, List[Tuple[float, float]]]:
        subscription = {'channel': 'orderbook', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        if self._orderbook_timestamps[market] == 0:
            self.wait_for_orderbook_update(market, 5)
        return {
            side: sorted(
                [(price, quantity) for price, quantity in list(self._orderbooks[market][side].items())
                 if quantity],
                key=lambda order: order[0] * (-1 if side == 'bids' else 1)
            )
            for side in {'bids', 'asks'}
        }

    def get_orderbook_timestamp(self, market: str) -> float:
        return self._orderbook_timestamps[market]

    def wait_for_orderbook_update(self, market: str, timeout: Optional[float]) -> None:
        subscription = {'channel': 'orderbook', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        self._orderbook_update_events[market].wait(timeout)

    def get_ticker(self, market: str) -> Dict:
        subscription = {'channel': 'ticker', 'market': market}
        if subscription not in self._subscriptions:
            self._subscribe(subscription)
        return self._tickers[market]

    def _handle_orderbook_message(self, message: Dict) -> None:
        market = message['market']
        subscription = {'channel': 'orderbook', 'market': market}
        if subscription not in self._subscriptions:
            return
        data = message['data']
        if data['action'] == 'partial':
            self._reset_orderbook(market)
        for side in {'bids', 'asks'}:
            book = self._orderbooks[market][side]
            for price, size in data[side]:
                if size:
                    book[price] = size
                else:
                    del book[price]
            self._orderbook_timestamps[market] = data['time']
        checksum = data['checksum']
        orderbook = self.get_orderbook(market)
        checksum_data = [
            ':'.join([f'{float(order[0])}:{float(order[1])}' for order in (bid, offer) if order])
            for (bid, offer) in zip_longest(orderbook['bids'][:100], orderbook['asks'][:100])
        ]

        computed_result = int(zlib.crc32(':'.join(checksum_data).encode()))
        if computed_result != checksum:
            self._last_received_orderbook_data_at = 0
            self._reset_orderbook(market)
            self._unsubscribe({'market': market, 'channel': 'orderbook'})
            self._subscribe({'market': market, 'channel': 'orderbook'})
        else:
            self._orderbook_update_events[market].set()
            self._orderbook_update_events[market].clear()

    def _handle_trades_message(self, message: Dict) -> None:
        self._trades[message['market']].append(message['data'])

    def _handle_ticker_message(self, message: Dict) -> None:
        self._tickers[message['market']] = message['data']

    def _handle_fills_message(self, message: Dict) -> None:
        self._fills.append(message['data'])

    def _handle_orders_message(self, message: Dict) -> None:
        data = message['data']
        self._orders.update({data['id']: data})

    def _on_message(self, ws, raw_message: str) -> None:
        message = json.loads(raw_message)
        message_type = message['type']
        if message_type in {'subscribed', 'unsubscribed'}:
            return
        elif message_type == 'info':
            if message['code'] == 20001:
                return self.reconnect()
        elif message_type == 'error':
            raise Exception(message)
        channel = message['channel']

        if channel == 'orderbook':
            self._handle_orderbook_message(message)
        elif channel == 'trades':
            self._handle_trades_message(message)
        elif channel == 'ticker':
            self._handle_ticker_message(message)
        elif channel == 'fills':
            self._handle_fills_message(message)
        elif channel == 'orders':
            self._handle_orders_message(message)