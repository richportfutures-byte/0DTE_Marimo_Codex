# Sanitized Schwab Option-Chain Shape

Sanitized fixture; not live; not broker data after sanitization; for parser design only.

```text
shape_summary:
  top_level_keys: [assetMainType, assetSubType, callExpDateMap, daysToExpiration, dividendYield, interestRate, interval, isChainTruncated, isDelayed, isIndex, numberOfContracts, putExpDateMap, status, strategy, symbol, underlying, underlyingPrice, volatility]
  call_map_key: callExpDateMap
  put_map_key: putExpDateMap
  call_expiry_keys: [2026-05-04:2]
  put_expiry_keys: [2026-05-04:2]
  call_strike_keys: [7230.0, 7235.0]
  put_strike_keys: [7230.0, 7235.0]
  contract_fields: [ask, askSize, bid, bidAskSize, bidSize, change, close, closePrice, daysToExpiration, delayed, deliverableNote, delta, description, exchangeName, exerciseType, expirationDate, expirationType, extrinsicValue, fiftyTwoWeekHigh, fiftyTwoWeekLow, gamma, high52Week, highPrice, inTheMoney, intrinsicValue, last, lastSize, lastTradingDay, low52Week, lowPrice, mark, markChange, markPercentChange, mini, multiplier, netChange, nonStandard, openInterest, openPrice, optionDeliverablesList, optionRoot, pennyPilot, percentChange, putCall, quoteTime, quoteTimeInLong, rho, settlementType, strikePrice, symbol, theoreticalOptionValue, theoreticalVolatility, theta, timeValue, totalVolume, tradeTime, tradeTimeInLong, vega, volatility]
```
