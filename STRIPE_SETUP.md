# Stripe Payment Gateway Setup Guide

This guide will help you set up Stripe payment gateway for the chatbot subscription system.

## Prerequisites

1. A Stripe account (sign up at https://stripe.com)
2. Python backend running
3. React Native frontend configured

## Backend Setup

### 1. Install Dependencies

```bash
cd Backend_Python
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update your `.env` file with the following Stripe configuration:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Stripe Price IDs (create these in Stripe Dashboard)
STRIPE_BASIC_PRICE_ID=price_basic_plan_id
STRIPE_STANDARD_PRICE_ID=price_standard_plan_id
STRIPE_PREMIUM_PRICE_ID=price_premium_plan_id
```

### 3. Create Stripe Products and Prices

1. Go to https://dashboard.stripe.com/test/products
2. Create three products with the following details:

**Basic Plan:**
- Name: Basic Plan
- Price: $10.00 USD
- Billing period: Monthly
- Copy the Price ID and set it as `STRIPE_BASIC_PRICE_ID`

**Standard Plan:**
- Name: Standard Plan
- Price: $20.00 USD
- Billing period: Monthly
- Copy the Price ID and set it as `STRIPE_STANDARD_PRICE_ID`

**Premium Plan:**
- Name: Premium Plan
- Price: $30.00 USD
- Billing period: Monthly
- Copy the Price ID and set it as `STRIPE_PREMIUM_PRICE_ID`

### 4. Get Your API Keys

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Publishable key** and set it as `STRIPE_PUBLISHABLE_KEY`
3. Copy your **Secret key** and set it as `STRIPE_SECRET_KEY`

### 5. Set Up Webhooks

1. Go to https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. Set the endpoint URL to: `https://your-backend-url.com/api/subscription/webhook`
4. Select the following events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Signing secret** and set it as `STRIPE_WEBHOOK_SECRET`

### 6. Run Database Migrations

```bash
cd Backend_Python
alembic upgrade head
```

### 7. Start the Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd Frontend_CLI
npm install
```

This will install `@stripe/stripe-react-native` along with other dependencies.

### 2. Configure Environment Variables

Update your `.env` file:

```env
API_URL=http://your-backend-url:8000
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

### 3. iOS Setup (if using iOS)

```bash
cd ios
pod install
cd ..
```

### 4. Run the App

**Android:**
```bash
npm run android
```

**iOS:**
```bash
npm run ios
```

## Testing the Integration

### Test Cards

Use these test card numbers in Stripe Checkout:

- **Success:** 4242 4242 4242 4242
- **Decline:** 4000 0000 0000 0002
- **3D Secure:** 4000 0025 0000 3155

Use any future expiration date, any 3-digit CVC, and any postal code.

### Test Flow

1. **Free Plan (Default):**
   - New users start with 1 message per week
   - After sending 1 message, subscription modal appears

2. **Purchase Subscription:**
   - Navigate to Settings → Manage Subscription
   - Select a plan (Basic, Standard, or Premium)
   - Click "Subscribe Now"
   - Complete payment in browser
   - Return to app

3. **Use Chatbot:**
   - Go to Chatbot tab
   - Send messages according to your plan limit
   - Messages remaining counter updates after each message

4. **Cancel Subscription:**
   - Go to Subscription screen
   - Click "Cancel Subscription"
   - Subscription continues until end of billing period
   - Then reverts to free plan

## Subscription Plans

| Plan | Price | Messages/Week |
|------|-------|---------------|
| Free | $0 | 1 |
| Basic | $10 | 10 |
| Standard | $20 | 20 |
| Premium | $30 | 30 |

## API Endpoints

- `GET /api/subscription/plans` - Get all available plans
- `GET /api/subscription/my-subscription` - Get current user's subscription
- `POST /api/subscription/create-checkout-session` - Create Stripe checkout session
- `POST /api/subscription/cancel` - Cancel subscription
- `POST /api/subscription/webhook` - Stripe webhook handler

## Troubleshooting

### Webhook Not Working

1. For local development, use Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:8000/api/subscription/webhook
   ```
2. Copy the webhook signing secret and update `STRIPE_WEBHOOK_SECRET`

### Payment Not Processing

1. Check Stripe Dashboard logs
2. Verify API keys are correct
3. Ensure webhook endpoint is accessible
4. Check backend logs for errors

### Subscription Not Updating

1. Verify webhook events are being received
2. Check database for subscription record
3. Ensure user_id metadata is being passed correctly

## Production Deployment

### Before Going Live

1. **Switch to Live Mode:**
   - Create products in live mode
   - Update all API keys to live keys (remove `_test_`)
   - Update webhook endpoint to production URL

2. **Security:**
   - Use HTTPS for all endpoints
   - Secure your webhook endpoint
   - Never expose secret keys in frontend

3. **Testing:**
   - Test complete flow in live mode with real cards
   - Verify webhooks are working
   - Test subscription cancellation

## Support

For issues with:
- **Stripe Integration:** Check Stripe Dashboard logs
- **Backend Errors:** Check FastAPI logs
- **Frontend Issues:** Check React Native debugger

## Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe React Native](https://github.com/stripe/stripe-react-native)
