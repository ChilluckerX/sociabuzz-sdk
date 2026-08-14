# Fee & Tax Reference — SociaBuzz Payment Gateway

> Live fee data fetched directly from the SociaBuzz payment API.
> Last updated: 2026-08-12 05:28 UTC

This document lists the **transaction fee / tax** charged by SociaBuzz for
every supported country and payment method.  Fees are charged **per
transaction** on top of the donation amount (the donor pays the fee).

## Fee Types

| Type | Meaning |
|------|---------|
| `percent` | A percentage of the donation amount |
| `nominal` | A fixed flat fee regardless of amount |
| `percent_and_amount` | Percentage **plus** a fixed amount |
| `percent_or_amount` | Percentage **or** a fixed amount — whichever is higher |

## How Fees Are Calculated

```
Donor pays  =  Donation amount  +  Transaction fee

percent             →  fee = amount × rate
nominal             →  fee = fixed_amount
percent_and_amount  →  fee = (amount × rate) + fixed_amount
percent_or_amount   →  fee = max(amount × rate, fixed_amount)
```

## Query Fees Programmatically

### REST API

```bash
# List supported countries
curl http://localhost:8000/api/fees/countries

# Get live fees for a country + amount
curl -X POST http://localhost:8000/api/fees \
  -H "Content-Type: application/json" \
  -d '{"country":"Malaysia","amount":5.0}'
```

### Python SDK

```python
import asyncio
from sociabuzz import FeeCalculator

async def main():
    calc = FeeCalculator(username="your_creator_username")
    estimates = await calc.estimate(country='Malaysia', amount=5.0)
    for e in estimates:
        print(f'{e.label:<22} fee={e.fee.total_fee:>8}  pay={e.fee.total_pay:>8}')
    await calc.close()

asyncio.run(main())
```

### Sample Output (Malaysia, MYR 5.00)

```
Touch & Go             fee=    0.09  pay=    5.09
GrabPay (Malaysia)     fee=    0.06  pay=    5.06
ShopeePay (Malaysia)   fee=    0.06  pay=    5.06
FPX                    fee=    0.99  pay=    5.99
Bitcoin                fee=    0.05  pay=    5.05
...
```

## Summary by Country

| Country | Currency | Methods | Cheapest Method | Sample Fee |
|---------|----------|---------|-----------------|------------|
| Malaysia | MYR | 10 | Bitcoin | MYR 0.05 |
| Indonesia | IDR | 24 | QRIS | IDR 65 |
| Singapore | SGD | 8 | Bitcoin | SGD 0.05 |
| Philippines | PHP | 16 | Bank Redirect | PHP 0.03 |
| Thailand | THB | 12 | PromptPay QR | THB 0.90 |
| Pakistan | PKR | 6 | Bitcoin | PKR 5.13 |
| Bangladesh | BDT | 6 | Bitcoin | BDT 0.04 |
| Sri Lanka | LKR | 6 | Bitcoin | LKR 0.03 |
| United Arab Emirates | AED | 6 | Bitcoin | AED 0.06 |
| Saudi Arabia | SAR | 6 | Bitcoin | SAR 0.06 |
| Qatar | QAR | 6 | Bitcoin | QAR 0.06 |
| Nigeria | NGN | 0 | — | — |
| South Africa | ZAR | 6 | Bitcoin | ZAR 0.51 |
| United Kingdom | GBP | 6 | Bitcoin | GBP 0.05 |
| Denmark | DKK | 6 | Bitcoin | DKK 0.51 |
| Australia | AUD | 6 | Bitcoin | AUD 0.05 |
| New Zealand | NZD | 6 | Bitcoin | NZD 0.05 |
| United States | USD | 6 | Bitcoin | USD 0.05 |

---

## Detailed Fee Tables

### Southeast Asia

#### MY Malaysia (MYR)

_Sample amount: MYR 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Touch & Go | `my_touchngo` | E-Wallet | xendit | percent | 1.7% | 0.09 | 5.09 | 1.0 | 5090.0 |
| 2 | GrabPay (Malaysia) | `my_grabpay` | E-Wallet | xendit | percent | 1.2% | 0.06 | 5.06 | 1.0 | 1500.0 |
| 3 | ShopeePay (Malaysia) | `my_shopeepay` | E-Wallet | xendit | percent | 1.2% | 0.06 | 5.06 | 1.0 | 4999.0 |
| 4 | FPX | `my_fpx` | Bank Transfer | xendit | nominal | 0.99 flat | 0.99 | 5.99 | 1.0 | 5000.0 |
| 5 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |
| 6 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |
| 7 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |
| 8 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |
| 9 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |
| 10 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.05 | 0.38 | 1911.91 |

#### ID Indonesia (IDR)

_Sample amount: IDR 10000.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Gopay | `gopay` | E-Wallet | midtrans | percent | 2% | 190 | 9513 | 1000.0 | 20000000.0 |
| 2 | OVO | `ovo` | E-Wallet | xendit | percent | 1.665% | 158 | 9481 | 1000.0 | 20000000.0 |
| 3 | DANA | `dana` | E-Wallet | xendit | percent | 1.665% | 158 | 9481 | 1000.0 | 20000000.0 |
| 4 | LinkAja | `linkaja` | E-Wallet | xendit | percent | 1.665% | 158 | 9481 | 1000.0 | 20000000.0 |
| 5 | JeniusPay | `jeniuspay` | E-Wallet | xendit | percent | 2.22% | 212 | 9535 | 1000.0 | 5000000.0 |
| 6 | AstraPay | `astrapay` | E-Wallet | xendit | percent | 1.665% | 158 | 9481 | 1000.0 | 20000000.0 |
| 7 | ShopeePay | `shopeepay_idr` | E-Wallet | 2c2p | percent | 2.22% | 213 | 9536 | 1000.0 | 20000000.0 |
| 8 | QRIS | `qris` | QRIS | xendit | percent | 0.7% | 65 | 9389 | 1000.0 | 10000000.0 |
| 9 | BCA | `bca` | Bank Transfer | midtrans | nominal | 4975 flat | 4975 | 14,298 | 10000.0 | 50000000.0 |
| 10 | Mandiri | `mandiri` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 11 | BRI | `bri` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 12 | BNI | `bni` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 13 | BSI | `bsi` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 14 | CIMB Niaga | `cimb` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 15 | Permata | `permata` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 16 | BJB | `bjb` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 17 | Bank Neo Commerce | `bnc` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 18 | Bank Sahabat Sampoerna | `sahabat_sampoerna` | Bank Transfer | xendit | nominal | 4440 flat | 4440 | 13,763 | 10000.0 | 50000000.0 |
| 19 | Indomaret | `indomaret` | Retail Outlet | xendit | nominal | 14000 flat | 14,000 | 23,323 | 10000.0 | 5000000.0 |
| 20 | Alfamart | `alfamart` | Retail Outlet | xendit | nominal | 5550 flat | 5550 | 14,873 | 10000.0 | 2500000.0 |
| 21 | Alfamidi | `alfamidi` | Retail Outlet | xendit | nominal | 5550 flat | 5550 | 14,873 | 10000.0 | 2500000.0 |
| 22 | Alfa Express | `alfaexpress` | Retail Outlet | xendit | nominal | 5550 flat | 5550 | 14,873 | 10000.0 | 2500000.0 |
| 23 | Lawson | `lawson` | Retail Outlet | xendit | nominal | 5550 flat | 5550 | 14,873 | 10000.0 | 2500000.0 |
| 24 | DAN+DAN | `dandan` | Retail Outlet | xendit | nominal | 5550 flat | 5550 | 14,873 | 10000.0 | 2500000.0 |

#### SG Singapore (SGD)

_Sample amount: SGD 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | PayNow QR | `paynow_sgd` | E-Wallet | tazapay | percent | 1.8% | 0.09 | 5.11 | 1.0 | 250.0 |
| 2 | GrabPay (Singapore) | `grabpay_stripe` | E-Wallet | stripe | percent_and_amount | 3.564% + 0.01 | 0.20 | 5.22 | 1.0 | 250.0 |
| 3 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |
| 4 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |
| 5 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |
| 6 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |
| 7 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |
| 8 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.07 | 0.11 | 598.41 |

#### PH Philippines (PHP)

_Sample amount: PHP 100.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | GCash | `gcash` | E-Wallet | xendit | percent | 2.576% | 2.54 | 98.65 | 1.0 | 10000.0 |
| 2 | Paymaya | `paymaya` | E-Wallet | xendit | percent | 2.016% | 1.98 | 98.09 | 1.0 | 10000.0 |
| 3 | GrabPay (Philippines) | `grabpay` | E-Wallet | xendit | percent | 2.24% | 2.20 | 98.31 | 1.0 | 10000.0 |
| 4 | ShopeePay (Philippines) | `shopeepay_php` | E-Wallet | xendit | percent | 2.24% | 2.20 | 98.31 | 1.0 | 10000.0 |
| 5 | QR Ph | `qrph` | QRIS | xendit | percent_or_amount | 1.168% or 16.8 (whichever higher) | 16.80 | 112.91 | 1.0 | 10000.0 |
| 6 | BPI | `bpi` | Direct Debit | xendit | percent_or_amount | 1.12% or 16.8 (whichever higher) | 16.80 | 112.91 | 30.0 | 10000.0 |
| 7 | UBP | `ubp` | Direct Debit | xendit | percent_or_amount | 1.12% or 16.8 (whichever higher) | 16.80 | 112.91 | 30.0 | 10000.0 |
| 8 | RCBC | `rcbc` | Direct Debit | xendit | percent_or_amount | 1.12% or 16.8 (whichever higher) | 16.80 | 112.91 | 30.0 | 10000.0 |
| 9 | Bank Redirect | `bank_push_php` | Bank Redirect | tazapay | percent | 1.8% | 0.03 | 1.70 | 1.0 | 200.0 |
| 10 | Cebuana Lhuillier | `cebuana` | Retail Outlet | xendit | nominal | 28 flat | 28 | 124.11 | 1.0 | 10000.0 |
| 11 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |
| 12 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |
| 13 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |
| 14 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |
| 15 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |
| 16 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.97 | 97.08 | 5.72 | 28629.91 |

#### TH Thailand (THB)

_Sample amount: THB 100.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | PromptPay QR | `th_promptpay` | E-Wallet | xendit | percent | 0.856% | 0.90 | 104.96 | 5.0 | 10000.0 |
| 2 | LINE Pay | `th_linepay` | E-Wallet | xendit | percent | 3.424% | 3.69 | 107.75 | 5.0 | 10000.0 |
| 3 | TrueMoney | `th_truemoney` | E-Wallet | xendit | percent | 3.424% | 3.69 | 107.75 | 5.0 | 10000.0 |
| 4 | ShopeePay (Thailand) | `th_shopeepay` | E-Wallet | xendit | percent | 3.424% | 3.69 | 107.75 | 5.0 | 10000.0 |
| 5 | Alipay | `ap` | E-Wallet | dlocal | percent | 3.3705% | 3.63 | 107.69 | 5.0 | 5000.0 |
| 6 | WeChat Pay | `th_wechatpay` | E-Wallet | xendit | percent | 1.605% | 1.70 | 105.76 | 5.0 | 10000.0 |
| 7 | Big C | `tk` | Bank Transfer | dlocal | percent | 2.4075% | 2.57 | 106.63 | 5.0 | 10000.0 |
| 8 | Bangkok Bank | `bbl_mobile_banking` | Bank Transfer | xendit | nominal | 16.05 flat | 16.05 | 120.11 | 20.0 | 10000.0 |
| 9 | Kasikornbank | `kbank_mobile_banking` | Bank Transfer | xendit | nominal | 16.05 flat | 16.05 | 120.11 | 20.0 | 10000.0 |
| 10 | Krungthai Bank | `ktb_mobile_banking` | Bank Transfer | xendit | nominal | 16.05 flat | 16.05 | 120.11 | 20.0 | 10000.0 |
| 11 | Krungsri | `krungsri_mobile_banking` | Bank Transfer | xendit | nominal | 16.05 flat | 16.05 | 120.11 | 20.0 | 10000.0 |
| 12 | Siam Commercial Bank | `scb_mobile_banking` | Bank Transfer | xendit | nominal | 16.05 flat | 16.05 | 120.11 | 20.0 | 10000.0 |

### South Asia

#### PK Pakistan (PKR)

_Sample amount: PKR 500.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 5.13 | 513.11 | 25.96 | 129821.57 |

#### BD Bangladesh (BDT)

_Sample amount: BDT 500.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.04 | 4.49 | 0.1 | 500.0 |

#### LK Sri Lanka (LKR)

_Sample amount: LKR 1000.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.03 | 3.11 | 0.1 | 500.0 |

### Middle East

#### AE United Arab Emirates (AED)

_Sample amount: AED 20.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |

#### SA Saudi Arabia (SAR)

_Sample amount: SAR 20.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.65 | 0.1 | 500.0 |

#### QA Qatar (QAR)

_Sample amount: QAR 20.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.06 | 5.93 | 0.1 | 500.0 |

### Africa

#### NG Nigeria (NGN)

_Sample amount: NGN 2000.0_

> No active payment methods available for this country at the sample amount.

#### ZA South Africa (ZAR)

_Sample amount: ZAR 50.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.31 | 1.51 | 7565.0 |

### Europe

#### GB United Kingdom (GBP)

_Sample amount: GBP 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.08 | 0.06 | 345.92 |

#### DK Denmark (DKK)

_Sample amount: DKK 50.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.51 | 51.32 | 0.6 | 3028.22 |

### Oceania

#### AU Australia (AUD)

_Sample amount: AUD 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.23 | 0.13 | 661.58 |

#### NZ New Zealand (NZD)

_Sample amount: NZD 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 4.94 | 0.15 | 796.3 |

### Americas

#### US United States (USD)

_Sample amount: USD 5.0_

| # | Method | Key | Group | Gateway | Fee Type | Fee | Total Fee | Donor Pays | Min | Max |
|---|--------|-----|-------|---------|----------|-----|-----------|------------|-----|-----|
| 1 | Bitcoin | `btc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |
| 2 | Ethereum | `eth` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |
| 3 | Tether (USDT) | `usdt` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |
| 4 | USD Coin (USDC) | `usdc` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |
| 5 | PayPal USD (PYUSD) | `pyusd` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |
| 6 | Binance Pay | `binance` | Crypto | triplea | percent_or_amount | 1% or 0.01 (whichever higher) | 0.05 | 5.01 | 0.1 | 500.0 |

---

## Notes

- All fees are **borne by the donor** (added on top of the donation amount).
- Fees are returned **live** by SociaBuzz and may change without notice.
- `min` / `max` columns show the supported transaction range per method.
- Crypto fees (`percent_or_amount`) use the higher of 1% or a small fixed floor.
- Nigeria currently exposes no active local methods at the sample amount.
- Stripe credit-card availability depends on the creator's account configuration.

