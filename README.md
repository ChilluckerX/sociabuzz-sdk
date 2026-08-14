# SociaBuzz Payment API

Reverse-engineered wrapper for the [SociaBuzz](https://sociabuzz.com) donation flow.  
Exposes **6 clean REST endpoints** so you can integrate SociaBuzz donations into any platform.

> **18 countries supported** — from Malaysia/Indonesia to US/UK/Australia and more.  
> See [`docs/FEES.md`](docs/FEES.md) for the full fee/tax reference per country per transaction.

> **Unofficial project.** This SDK was built by observing SociaBuzz's public donation
> flow — it is not affiliated with, endorsed by, or supported by SociaBuzz. The upstream
> flow can change without notice and break this SDK. Use at your own risk; no warranty
> is provided (see [LICENSE](LICENSE)).

---

## Supported Countries

| Region | Country | Currency | Local Methods | Card/Crypto |
|--------|---------|----------|---------------|-------------|
| **SE Asia** | 🇲🇾 Malaysia | MYR | TNG, GrabPay, ShopeePay, FPX | ✅ |
| | 🇮🇩 Indonesia | IDR | GoPay, OVO, DANA, QRIS, 12 banks, 6 retail | ✅ |
| | 🇸🇬 Singapore | SGD | PayNow QR, GrabPay | ✅ |
| | 🇵🇭 Philippines | PHP | GCash, Paymaya, GrabPay, ShopeePay, QR Ph, BPI, Cebuana | ✅ |
| | 🇹🇭 Thailand | THB | PromptPay, LINE Pay, TrueMoney, ShopeePay, 5 banks | ✅ |
| **South Asia** | 🇵🇰 Pakistan | PKR | — | ✅ |
| | 🇧🇩 Bangladesh | BDT | — | Card only |
| | 🇱🇰 Sri Lanka | LKR | — | Card only |
| **Middle East** | 🇦🇪 UAE | AED | — | Card + GPay/APay |
| | 🇸🇦 Saudi Arabia | SAR | — | Card only |
| | 🇶🇦 Qatar | QAR | — | Card only |
| **Africa** | 🇳🇬 Nigeria | NGN | — | Card only |
| | 🇿🇦 South Africa | ZAR | — | ✅ |
| **Europe** | 🇬🇧 United Kingdom | GBP | — | ✅ |
| | 🇩🇰 Denmark | DKK | — | ✅ |
| **Oceania** | 🇦🇺 Australia | AUD | — | ✅ |
| | 🇳🇿 New Zealand | NZD | — | ✅ |
| **Americas** | 🇺🇸 United States | USD | — | ✅ |

> **✅** = Credit Card + Google Pay + Apple Pay + Crypto (BTC, ETH, USDT, USDC, PYUSD, Binance)

---

## Quick Start

```bash
git clone https://github.com/yourusername/sociabuzz-sdk.git
cd sociabuzz-sdk
pip install -r requirements.txt          # or: pip install -e .[server]
cp .env.example .env          # edit DEFAULT_CREATOR + API_KEY
python main.py                # http://localhost:8000
```

Interactive docs → **http://localhost:8000/docs**

---

## Install as a Package

The SDK is also installable standalone (without the server):

```bash
pip install -e .            # SDK only (httpx + pydantic)
pip install -e .[server]    # SDK + FastAPI server
pip install -e .[dev]       # + ruff / mypy for linting
```

---

## Flow Overview

```
Step 0 (optional)   Step 1              Step 2               Step 3              Step 4
─────────────────   ──────              ──────               ──────              ──────
POST /api/fees  ──► POST /api/donate ──► POST /api/payment ─► POST /api/payment ► POST /api/payment
GET  /countries       (token)              /methods             /create             /status

Check fees       Submit donation     List available       Pick a method &     Poll until
before donating  (country, amount,   payment methods      get payment URL     paid / expired
                 name, email)        (numbered list)      to redirect user
     │                  │                  │                    │                  │
     ▼                  ▼                  ▼                    ▼                  ▼
 Returns: fee     Returns: token     Returns: numbered    Returns: payment   Returns: status
 table per        (use in all        method list          URL / QR code      (pending/paid/
 country/method   subsequent steps)  with fees                               expired/failed)
```

---

## API Reference

### Step 0 — Check Fees (optional)

Query the fee/tax for every payment method **before** creating a donation. Nothing is charged.

`POST /api/fees`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `country` | string | | Country name (default: `Malaysia`) |
| `amount` | number | ✅ | Donation amount in local currency |
| `username` | string | | Creator username (default: `your_creator_username`) |

**Request:**
```json
{ "country": "Malaysia", "amount": 5.0 }
```

**Response:**
```json
{
  "success": true,
  "country": "Malaysia",
  "currency": "MYR",
  "amount": 5.0,
  "methods": [
    {
      "id": 1, "name": "my_touchngo", "label": "Touch & Go",
      "group": "E-Wallet", "gateway": "xendit",
      "currency": "MYR", "amount": 5.0,
      "fee": {
        "fee_type": "percent", "fee_rate": 0.017, "fee_fixed": 0,
        "total_fee": "0.09", "total_pay": "5.09",
        "min_amount": 1.0, "max_amount": 5090.0
      }
    }
  ],
  "total": 10
}
```

> **GET /api/fees/countries** — returns the full list of supported countries with currencies & ISO codes.

> See [`docs/FEES.md`](docs/FEES.md) for the complete static fee reference table.

---

### Step 1 — Submit Donation

`POST /api/donate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | ✅ | Creator's SociaBuzz username |
| `amount` | number | ✅ | Donation amount |
| `country` | string | ✅ | Country name (see table above) — currency is auto-detected |
| `fullname` | string | ✅ | Donor's display name |
| `email` | string | ✅ | Donor's email address |
| `note` | string | | Optional message |

**Request:**
```json
{
  "username": "your_creator_username",
  "amount": 5.00,
  "country": "Malaysia",
  "fullname": "John Doe",
  "email": "john@example.com",
  "note": "Love your content!"
}
```

**Response:**
```json
{
  "success": true,
  "token": "82c53d48-3343-11f1-8924-cee239a73494",
  "country": "Malaysia",
  "currency": "MYR",
  "amount": 5.0,
  "redirect_url": "https://sociabuzz.com/payment/x/82c53d48-...",
  "expires_in": 3600
}
```

---

### Step 2 — List Payment Methods

`POST /api/payment/methods`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | ✅ | Token from Step 1 |

**Request:**
```json
{
  "token": "82c53d48-3343-11f1-8924-cee239a73494"
}
```

<details>
<summary><b>🇲🇾 Malaysia Response (example)</b></summary>

```json
{
  "success": true,
  "token": "82c53d48-...",
  "country": "Malaysia",
  "currency": "MYR",
  "amount": 5.0,
  "methods": [
    { "id": 1,  "name": "my_touchngo",        "label": "Touch & Go",          "group": "E-Wallet",      "gateway": "xendit"  },
    { "id": 2,  "name": "grab_myr",            "label": "GrabPay (Malaysia)", "group": "E-Wallet",      "gateway": "xendit"  },
    { "id": 3,  "name": "my_shopeepay",        "label": "ShopeePay (Malaysia)","group": "E-Wallet",     "gateway": "2c2p"    },
    { "id": 4,  "name": "my_fpx",              "label": "FPX",                "group": "Bank Transfer", "gateway": "xendit"  },
    { "id": 5,  "name": "credit_card_stripe",  "label": "Credit Card",        "group": "Card",          "gateway": "stripe"  },
    { "id": 6,  "name": "googlepay_stripe",    "label": "Google Pay",         "group": "E-Wallet",      "gateway": "stripe"  },
    { "id": 7,  "name": "applepay_stripe",     "label": "Apple Pay",          "group": "E-Wallet",      "gateway": "stripe"  },
    { "id": 8,  "name": "btc",                 "label": "Bitcoin",            "group": "Crypto",        "gateway": "triplea" },
    { "id": 9,  "name": "eth",                 "label": "Ethereum",           "group": "Crypto",        "gateway": "triplea" },
    { "id": 10, "name": "usdt",                "label": "Tether (USDT)",      "group": "Crypto",        "gateway": "triplea" },
    { "id": 11, "name": "usdc",                "label": "USD Coin (USDC)",    "group": "Crypto",        "gateway": "triplea" },
    { "id": 12, "name": "pyusd",               "label": "PayPal USD (PYUSD)", "group": "Crypto",        "gateway": "triplea" },
    { "id": 13, "name": "binance",             "label": "Binance Pay",        "group": "Crypto",        "gateway": "triplea" }
  ],
  "total": 13
}
```
</details>

<details>
<summary><b>🇮🇩 Indonesia Response (example)</b></summary>

```json
{
  "success": true,
  "token": "7abc211c-...",
  "country": "Indonesia",
  "currency": "IDR",
  "amount": 10000,
  "methods": [
    { "id": 1,  "name": "gopay",               "label": "GoPay",               "group": "E-Wallet",      "gateway": "midtrans" },
    { "id": 2,  "name": "ovo",                  "label": "OVO",                 "group": "E-Wallet",      "gateway": "xendit"   },
    { "id": 3,  "name": "dana",                 "label": "DANA",                "group": "E-Wallet",      "gateway": "xendit"   },
    { "id": 4,  "name": "linkaja",              "label": "LinkAja",             "group": "E-Wallet",      "gateway": "xendit"   },
    { "id": 5,  "name": "jeniuspay",            "label": "JeniusPay",           "group": "E-Wallet",      "gateway": "xendit"   },
    { "id": 6,  "name": "astrapay",             "label": "AstraPay",            "group": "E-Wallet",      "gateway": "xendit"   },
    { "id": 7,  "name": "shopeepay_idr",        "label": "ShopeePay",           "group": "E-Wallet",      "gateway": "2c2p"     },
    { "id": 8,  "name": "qris",                 "label": "QRIS",                "group": "QRIS",          "gateway": "xendit"   },
    { "id": 9,  "name": "bca",                  "label": "BCA",                 "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 10, "name": "mandiri",              "label": "Mandiri",             "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 11, "name": "bri",                  "label": "BRI",                 "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 12, "name": "bni",                  "label": "BNI",                 "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 13, "name": "bsi",                  "label": "BSI",                 "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 14, "name": "cimb",                 "label": "CIMB Niaga",          "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 15, "name": "maybank",              "label": "Maybank",             "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 16, "name": "permata",              "label": "Permata",             "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 17, "name": "bjb",                  "label": "BJB",                 "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 18, "name": "bnc",                  "label": "Bank Neo Commerce",   "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 19, "name": "sinarmas",             "label": "Bank Sinarmas",       "group": "Bank Transfer", "gateway": "xendit"   },
    { "id": 20, "name": "sahabat_sampoerna",    "label": "Bank Sahabat Sampoerna","group": "Bank Transfer","gateway": "xendit"  },
    { "id": 21, "name": "indomaret",            "label": "Indomaret",           "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 22, "name": "alfamart",             "label": "Alfamart",            "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 23, "name": "alfamidi",             "label": "Alfamidi",            "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 24, "name": "alfaexpress",          "label": "Alfa Express",        "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 25, "name": "lawson",               "label": "Lawson",              "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 26, "name": "dandan",               "label": "DAN+DAN",             "group": "Retail Outlet", "gateway": "xendit"   },
    { "id": 27, "name": "credit_card_stripe",   "label": "Credit Card",         "group": "Card",          "gateway": "stripe"   },
    { "id": 28, "name": "googlepay_stripe",     "label": "Google Pay",          "group": "E-Wallet",      "gateway": "stripe"   },
    { "id": 29, "name": "applepay_stripe",      "label": "Apple Pay",           "group": "E-Wallet",      "gateway": "stripe"   }
  ],
  "total": 29
}
```
</details>

---

### Step 3 — Create Payment

`POST /api/payment/create`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | ✅ | Token from Step 1 |
| `payment_method` | string | ✅ | Method `name` from Step 2 |

**Request:**
```json
{
  "token": "82c53d48-3343-11f1-8924-cee239a73494",
  "payment_method": "my_touchngo"
}
```

**Response:**
```json
{
  "success": true,
  "payment_method": "my_touchngo",
  "label": "Touch & Go",
  "gateway": "xendit",
  "fee": {
    "fee_type": "percent",
    "fee_rate": 0.017,
    "fee_fixed": 0,
    "total_fee": "0.09",
    "total_pay": "5.09",
    "min_amount": 1.0,
    "max_amount": 5090.0
  },
  "payment_url": "https://m.tngdigital.com.my/s/cashier/...",
  "qr_string": null,
  "token": "82c53d48-...",
  "inv_id": "TRIBE-MYR-260408-..."
}
```

> **Redirect the user to `payment_url`** to complete payment.
> For QRIS, display the `qr_string` as a QR code instead.

---

### Step 4 — Check Payment Status

`POST /api/payment/status`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | ✅ | Token from Step 1 |
| `inv_id` | string | ✅ | Invoice ID from Step 3 |
| `payment_method` | string | ✅ | Method used in Step 3 |

**Request:**
```json
{
  "token": "82c53d48-3343-11f1-8924-cee239a73494",
  "inv_id": "TRIBE-MYR-260408-...",
  "payment_method": "my_touchngo"
}
```

**Response:**
```json
{
  "success": true,
  "token": "82c53d48-...",
  "status": "paid"
}
```

| Status | Meaning |
|--------|---------|
| `pending` | Waiting for payment |
| `paid` | Payment completed ✅ |
| `expired` | Token/payment expired |
| `failed` | Payment failed |

---

## Integration Examples

### 🇲🇾 Malaysia — TNG eWallet (Python)

```python
import httpx, time

API = "http://localhost:8000"

# Step 1: Donate MYR 5
donate = httpx.post(f"{API}/api/donate", json={
    "username": "your_creator_username",
    "amount": 5.0,
    "country": "Malaysia",
    "fullname": "John Doe",
    "email": "john@example.com",
}).json()

token = donate["token"]
print(f"Token: {token}")
print(f"Amount: {donate['currency']} {donate['amount']}")

# Step 2: List methods
methods = httpx.post(f"{API}/api/payment/methods", json={
    "token": token,
}).json()

print(f"\nAvailable methods ({methods['total']}):")
for m in methods["methods"]:
    print(f"  {m['id']:>2}. {m['label']:<20} ({m['name']})")

# Step 3: Create payment with TNG
payment = httpx.post(f"{API}/api/payment/create", json={
    "token": token,
    "payment_method": "my_touchngo",     # pick from step 2
}).json()

print(f"\nFee: {payment['fee']['total_fee']}")
print(f"Total: {payment['fee']['total_pay']}")
print(f"Pay here: {payment['payment_url']}")

# Step 4: Poll status
while True:
    status = httpx.post(f"{API}/api/payment/status", json={
        "token": token,
        "inv_id": payment["inv_id"],
        "payment_method": "my_touchngo",
    }).json()
    print(f"Status: {status['status']}")
    if status["status"] in ("paid", "expired", "failed"):
        break
    time.sleep(5)
```

### 🇮🇩 Indonesia — GoPay (Python)

```python
import httpx, time

API = "http://localhost:8000"

# Step 1: Donate IDR 10,000
donate = httpx.post(f"{API}/api/donate", json={
    "username": "your_creator_username",
    "amount": 10000,
    "country": "Indonesia",
    "fullname": "Budi Santoso",
    "email": "budi@example.com",
}).json()

token = donate["token"]
print(f"Token: {token}")
print(f"Amount: {donate['currency']} {donate['amount']}")

# Step 2: List methods
methods = httpx.post(f"{API}/api/payment/methods", json={
    "token": token,
}).json()

print(f"\nAvailable methods ({methods['total']}):")
for m in methods["methods"]:
    print(f"  {m['id']:>2}. {m['label']:<25} [{m['group']}]")

# Step 3: Create payment with GoPay
payment = httpx.post(f"{API}/api/payment/create", json={
    "token": token,
    "payment_method": "gopay",            # pick from step 2
}).json()

print(f"\nFee: IDR {payment['fee']['total_fee']}")
print(f"Total: IDR {payment['fee']['total_pay']}")
print(f"Pay here: {payment['payment_url']}")

# Step 4: Poll status
while True:
    status = httpx.post(f"{API}/api/payment/status", json={
        "token": token,
        "inv_id": payment["inv_id"],
        "payment_method": "gopay",
    }).json()
    print(f"Status: {status['status']}")
    if status["status"] in ("paid", "expired", "failed"):
        break
    time.sleep(5)
```

### 🇹🇭 Thailand — PromptPay (Python)

```python
import httpx

API = "http://localhost:8000"

# Step 1: Donate THB 100
donate = httpx.post(f"{API}/api/donate", json={
    "username": "your_creator_username",
    "amount": 100,
    "country": "Thailand",
    "fullname": "Somchai",
    "email": "somchai@example.com",
}).json()

token = donate["token"]

# Step 2: List methods — will show PromptPay, LINE Pay, TrueMoney, banks, etc.
methods = httpx.post(f"{API}/api/payment/methods", json={"token": token}).json()
for m in methods["methods"]:
    print(f"  {m['id']:>2}. {m['label']}")

# Step 3: Create PromptPay payment
payment = httpx.post(f"{API}/api/payment/create", json={
    "token": token,
    "payment_method": "th_promptpay",
}).json()
print(f"Pay here: {payment['payment_url']}")
```

### cURL Example

```bash
# Step 1 — Donate
curl -X POST http://localhost:8000/api/donate \
  -H "Content-Type: application/json" \
  -d '{"username":"your_creator_username","amount":5,"country":"Malaysia","fullname":"Test","email":"test@test.com"}'

# Step 2 — List methods
curl -X POST http://localhost:8000/api/payment/methods \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN_HERE"}'

# Step 3 — Create payment
curl -X POST http://localhost:8000/api/payment/create \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN_HERE","payment_method":"my_touchngo"}'

# Step 4 — Check status
curl -X POST http://localhost:8000/api/payment/status \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN_HERE","inv_id":"TRIBE-MYR-...","payment_method":"my_touchngo"}'
```

---

## Payment Methods Reference

### 🇲🇾 Malaysia (MYR) — 13 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | Touch & Go | `my_touchngo` | Xendit | 1.7% |
| 2 | GrabPay | `grab_myr` | 2c2p | ~2.2% |
| 3 | ShopeePay | `my_shopeepay` | Xendit | ~1.2% |
| 4 | FPX (Online Banking) | `my_fpx` | Xendit | RM 0.99 flat |
| 5–7 | Credit Card / Google Pay / Apple Pay | `credit_card_stripe` / `googlepay_stripe` / `applepay_stripe` | Stripe | ~3.5% |
| 8–13 | BTC / ETH / USDT / USDC / PYUSD / Binance | `btc` / `eth` / `usdt` / `usdc` / `pyusd` / `binance` | TripleA | 1% |

### 🇮🇩 Indonesia (IDR) — 29 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| **E-Wallets** | | | | |
| 1 | GoPay | `gopay` | Midtrans | 2% |
| 2 | OVO | `ovo` | Xendit | 1.665% |
| 3 | DANA | `dana` | Xendit | 1.665% |
| 4 | LinkAja | `linkaja` | Xendit | 1.665% |
| 5 | JeniusPay | `jeniuspay` | Xendit | 2.22% |
| 6 | AstraPay | `astrapay` | Xendit | 1.665% |
| 7 | ShopeePay | `shopeepay_idr` | 2c2p | 1.665% |
| **QR** | | | | |
| 8 | QRIS | `qris` | Xendit | 0.7% |
| **Bank Transfer** | | | | |
| 9–20 | BCA / Mandiri / BRI / BNI / BSI / CIMB / Maybank / Permata / BJB / BNC / Sinarmas / Sahabat Sampoerna | see Step 2 | Xendit/Midtrans/Faspay | IDR 3,905–4,440 |
| **Retail** | | | | |
| 21–26 | Indomaret / Alfamart / Alfamidi / Alfa Express / Lawson / DAN+DAN | see Step 2 | Xendit | IDR 5,550–6,660 |
| **Card** | | | | |
| 27–29 | Credit Card / Google Pay / Apple Pay | see above | Stripe | ~3.5% |

### 🇸🇬 Singapore (SGD) — 11 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | PayNow QR | `paynow_sgd` | Tazapay | 1.8% |
| 2 | GrabPay | `grabpay_stripe` | Stripe | 3.56% + SGD 0.01 |
| 3–4 | Google Pay / Apple Pay | `googlepay_stripe` / `applepay_stripe` | Stripe | 10.8% + SGD 1.04 |
| 5 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |
| 6–11 | BTC / ETH / USDT / USDC / PYUSD / Binance | `btc` / `eth` / `usdt` / `usdc` / `pyusd` / `binance` | TripleA | 1% |

### 🇵🇭 Philippines (PHP) — 19 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| **E-Wallets** | | | | |
| 1 | GCash | `gcash` | Xendit | 2.58% |
| 2 | Paymaya | `paymaya` | Xendit | 2.02% |
| 3 | GrabPay | `grabpay` | Xendit | 2.24% |
| 4 | ShopeePay | `shopeepay_php` | Xendit | 2.24% |
| **QR / Direct Debit** | | | | |
| 5 | QR Ph | `qrph` | Xendit | 1.17% or PHP 16.80 |
| 6 | BPI (Direct Debit) | `bpi` | Xendit | 1.12% or PHP 16.80 |
| 7 | UBP (Direct Debit) | `ubp` | Xendit | 1.12% or PHP 16.80 |
| 8 | RCBC (Direct Debit) | `rcbc` | Xendit | 1.12% or PHP 16.80 |
| **Bank / Retail** | | | | |
| 9 | Bank Redirect | `bank_push_php` | Tazapay | 1.8% |
| 10 | Cebuana Lhuillier | `cebuana` | Xendit | PHP 28 flat |
| **Card** | | | | |
| 11 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |
| 12–13 | Google Pay / Apple Pay | `googlepay_stripe` / `applepay_stripe` | Stripe | 10.8% + PHP 1.04 |
| **Crypto** | | | | |
| 14–19 | BTC / ETH / USDT / USDC / PYUSD / Binance | `btc` / `eth` / `usdt` / `usdc` / `pyusd` / `binance` | TripleA | 1% |

### 🇹🇭 Thailand (THB) — 15 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| **E-Wallets** | | | | |
| 1 | PromptPay QR | `th_promptpay` | Xendit | 0.86% |
| 2 | LINE Pay | `th_linepay` | Xendit | 3.42% |
| 3 | TrueMoney | `th_truemoney` | Xendit | 3.42% |
| 4 | ShopeePay | `th_shopeepay` | Xendit | 3.42% |
| 5 | Alipay | `ap` | dLocal | 3.37% |
| 6 | WeChat Pay | `th_wechatpay` | Xendit | 1.6% |
| **Retail** | | | | |
| 7 | Big C | `tk` | dLocal | 2.41% |
| **Bank (Mobile Banking)** | | | | |
| 8 | Bangkok Bank | `bbl_mobile_banking` | Xendit | THB 16.05 flat |
| 9 | Kasikornbank | `kbank_mobile_banking` | Xendit | THB 16.05 flat |
| 10 | Krungthai Bank | `ktb_mobile_banking` | Xendit | THB 16.05 flat |
| 11 | Krungsri | `krungsri_mobile_banking` | Xendit | THB 16.05 flat |
| 12 | Siam Commercial Bank | `scb_mobile_banking` | Xendit | THB 16.05 flat |
| **Card** | | | | |
| 13–14 | Google Pay / Apple Pay | `googlepay_stripe` / `applepay_stripe` | Stripe | 10.8% + THB 1.04 |
| 15 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |

### 🇺🇸🇬🇧🇦🇺🇳🇿🇩🇰 US / UK / Australia / NZ / Denmark — 9 methods each

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |
| 2 | Google Pay | `googlepay_stripe` | Stripe | 10.8% + ~$1.04 equiv |
| 3 | Apple Pay | `applepay_stripe` | Stripe | 10.8% + ~$1.04 equiv |
| 4–9 | BTC / ETH / USDT / USDC / PYUSD / Binance | `btc` / `eth` / `usdt` / `usdc` / `pyusd` / `binance` | TripleA | 1% |

> Fixed fee amount varies by currency (USD $1.04, GBP £1.04, AUD $1.04, NZD $1.04, DKK kr 1.04).

### 🇵🇰🇿🇦 Pakistan / South Africa — 7 methods each

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |
| 2–7 | BTC / ETH / USDT / USDC / PYUSD / Binance | `btc` / `eth` / `usdt` / `usdc` / `pyusd` / `binance` | TripleA | 1% |

### 🇦🇪 UAE (AED) — 3 methods

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |
| 2 | Google Pay | `googlepay_stripe` | Stripe | 10.8% + AED 1.04 |
| 3 | Apple Pay | `applepay_stripe` | Stripe | 10.8% + AED 1.04 |

### 🇸🇦🇶🇦🇧🇩🇳🇬🇱🇰 Saudi Arabia / Qatar / Bangladesh / Nigeria / Sri Lanka — 1 method

| # | Method | Key | Gateway | Fee |
|---|--------|-----|---------|-----|
| 1 | Credit Card | `credit_card_stripe` | Stripe | ~3.5% |

---

## Project Structure

```
sociabuzz-sdk/
├── sociabuzz/              # SDK package (use standalone or via server)
│   ├── __init__.py         # Public exports: SociaBuzz, Donation, Payment, FeeCalculator, ...
│   ├── client.py           # SociaBuzz (entry point), Donation, Payment classes
│   ├── fees.py             # FeeCalculator, FeeEstimate (query fees without donating)
│   ├── _http.py            # Internal HTTP client (cookies, CSRF, requests)
│   ├── models.py           # FeeInfo, PaymentMethod (Pydantic models)
│   ├── constants.py        # SUPPORTED_COUNTRIES, GROUP_LABELS
│   └── exceptions.py       # SociaBuzzError hierarchy
│
├── server/                 # FastAPI REST server
│   ├── __init__.py         # create_app() factory
│   ├── app.py              # App factory, lifespan, health endpoint
│   ├── auth.py             # Optional API-key middleware (Bearer / X-API-Key)
│   ├── schemas.py          # Request/Response Pydantic models
│   ├── session.py          # Pluggable donation session store (memory or SQLite)
│   ├── webhook.py          # Background poller + callback_url webhook dispatch
│   └── routes/
│       ├── __init__.py     # Router aggregation
│       ├── donate.py       # POST /api/donate
│       ├── payment.py      # POST /api/payment/{methods,create,status}
│       └── fees.py         # POST /api/fees, GET /api/fees/countries
│
├── docs/
│   └── FEES.md             # Fee/tax reference per country per transaction
├── config.py               # Settings (env-driven)
├── main.py                 # Entry point: python main.py
├── pyproject.toml          # Installable package metadata (pip install -e .)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables (no real secrets — placeholders only)
└── README.md
```

> **No sensitive data is stored in this repo.** No captured cookies, session tokens, auth
> tokens, or debug dumps from real SociaBuzz sessions are included. `.env` (your real
> config) and any local `*.db` session files are git-ignored — see [`.gitignore`](.gitignore).

### SDK Usage (standalone)

```python
import asyncio
from sociabuzz import SociaBuzz

async def main():
    sb = SociaBuzz()
    donation = await sb.donate(
        username="creator", amount=5.0, country="Malaysia",
        fullname="John", email="john@test.com",
    )
    methods = await donation.get_payment_methods()
    for m in methods:
        print(f"{m.id}. {m.label} [{m.group}]")

    payment = await donation.create_payment("my_touchngo")
    print(f"Pay here: {payment.payment_url}")

    status = await payment.check_status()
    print(f"Status: {status}")

    await donation.close()

asyncio.run(main())
```

### Fee Calculator (standalone)

Query fees for any country + amount **without** creating a real donation:

```python
import asyncio
from sociabuzz import FeeCalculator

async def main():
    async with FeeCalculator(username="your_creator_username") as calc:
        estimates = await calc.estimate(country="Malaysia", amount=5.0)
        for e in estimates:
            print(f"{e.label:<22} fee={e.fee.total_fee:>8}  pay={e.fee.total_pay:>8}")

asyncio.run(main())
```

---

## How It Works (Under the Hood)

```
SDK (sociabuzz/)                  SociaBuzz Backend
────────────────                  ─────────────────
SociaBuzzHTTP.init_session()  ──► GET /{username}/tribe           → seeds ci_session + CSRF cookies
SociaBuzzHTTP.get_creator_config()
                              ──► GET /{username}/donate/queue    → fetches TRAKTIR_PRICE (unit price)
SociaBuzzHTTP.submit_donation()
                              ──► POST /{username}/donate/get-form-queue?buyme=1
                                                                  → returns payment token UUID
Donation._ensure_csrf()       ──► GET /payment/x/{token}          → seeds new ci_session + page CSRF
Donation.get_payment_methods()──► GET /payment/pay/setting        → returns available methods + fees
Donation.create_payment()     ──► POST /payment/send/create (JSON)→ returns payment URL / QR code
Payment.check_status()        ──► GET /payment/pending?type=...   → returns paid/pending/expired
```

Key implementation details:
- **CSRF**: Dual tokens — cookie (`sociabuzz_sb_cookie_csrf`) for donate, page-hidden-input (`sb_token_csrf`) for create
- **Amount**: In `buyme` mode, `amount = TRAKTIR_PRICE × qty` — server validates this
- **Body format**: `send/create` requires **JSON** body (not form-urlencoded)  
- **URL extraction**: Xendit returns `data.payment_link`, Midtrans returns `data.redirect_url`
