from typing import List, Dict, Optional, Tuple

from simulation.clock import Clock
from simulation.models.instrument import Instrument
from simulation.models.order import Order, OrderSide, OrderType
from simulation.models.portfolio import Portfolio
from simulation.strategy.base import BaseStrategy


class BuyLowSellHighStrategy(BaseStrategy):

    def __init__(self, instrument: Instrument, clock: Clock, portfolio: Portfolio, params: Dict):
        super(BuyLowSellHighStrategy, self).__init__(clock, portfolio)
        self.instrument = instrument
        base, quote = self.instrument.to_asset_instruments()
        self.base_wallet = self.portfolio.get_wallet(base)
        self.quote_wallet = self.portfolio.get_wallet(quote)
        self.local_min = None
        self.local_max = None

        self.buy_signal_thresh = params['buy_signal_thresh']
        self.sell_signal_thresh = params['sell_signal_thresh']

        self.three_vals = []

        self.is_buying = True

    def on_data_udf(self, data_event: Dict) -> Optional[List[Order]]:
        mid_price = data_event['mid_price'] # TODO query data_generator?
        self.three_vals.append(mid_price)
        if len(self.three_vals) > 3:
            self.three_vals.pop(0)

        if self._is_local_min():
            self.local_min = self.three_vals[1]

        if self._is_local_max():
            self.local_max = self.three_vals[1]

        if self.is_buying:
            if self.local_min is not None and mid_price - self.local_min > self.sell_signal_thresh * self.local_min:
                self.is_buying = False
                # reset old vals
                self.local_min = None
                self.local_max = None
                return [self.make_order(
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    instrument=self.instrument,
                    qty=0.9 * self.quote_wallet.free_balance() / mid_price,
                    price=mid_price
                )]
        else:
            if self.local_max is not None and self.local_max - mid_price > self.buy_signal_thresh * self.local_max:
                self.is_buying = True
                # reset old vals
                self.local_min = None
                self.local_max = None
                return [self.make_order(
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    instrument=self.instrument,
                    qty=0.9 * self.base_wallet.free_balance(),
                    price=mid_price
                )]

    def _is_local_min(self) -> bool:
        if len(self.three_vals) < 3:
            return False
        return self.three_vals[0] > self.three_vals[1] and self.three_vals[2] > self.three_vals[1]

    def _is_local_max(self) -> bool:
        if len(self.three_vals) < 3:
            return False
        return self.three_vals[0] < self.three_vals[1] and self.three_vals[2] < self.three_vals[1]
