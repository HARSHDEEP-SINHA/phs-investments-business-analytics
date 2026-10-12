-- PHS Business Intelligence portfolio: SQLite-compatible examples.
-- All underlying records are synthetic.

-- 1. Monthly inflows, outflows and net flows.
SELECT substr(transaction_date, 1, 7) AS month,
       SUM(CASE WHEN transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                THEN amount_inr ELSE 0 END) AS inflows_inr,
       SUM(CASE WHEN transaction_type IN ('REDEMPTION','SWITCH_OUT')
                THEN amount_inr ELSE 0 END) AS outflows_inr,
       SUM(CASE WHEN transaction_type IN ('PURCHASE','SIP_INSTALLMENT','SWITCH_IN')
                THEN amount_inr
                WHEN transaction_type IN ('REDEMPTION','SWITCH_OUT')
                THEN -amount_inr ELSE 0 END) AS net_flows_inr
FROM transactions
WHERE transaction_status = 'Successful'
GROUP BY substr(transaction_date, 1, 7)
ORDER BY month;

-- 2. Transacting clients by city.
SELECT c.city, COUNT(DISTINCT t.client_id) AS transacting_clients,
       SUM(t.amount_inr) AS transaction_amount_inr
FROM transactions t
JOIN clients c ON c.client_id = t.client_id
WHERE t.transaction_status = 'Successful'
GROUP BY c.city
ORDER BY transaction_amount_inr DESC;

-- 3. SIP registration status.
SELECT sip_status, COUNT(*) AS registrations,
       SUM(monthly_amount) AS registered_monthly_value_inr
FROM sips
GROUP BY sip_status
ORDER BY registrations DESC;

-- 4. Transaction failure rate by type.
SELECT transaction_type, COUNT(*) AS total_transactions,
       SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transactions,
       ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_pct
FROM transactions
GROUP BY transaction_type
ORDER BY failure_pct DESC;

-- 5. City ranking by net investment flows.
-- Positive amounts are inflows; redemptions and switch-outs are outflows.
WITH city_flows AS (
    SELECT
        c.city,
        SUM(CASE
            WHEN t.transaction_type IN (
                'PURCHASE', 'SIP_INSTALLMENT', 'SWITCH_IN'
            ) THEN t.amount_inr
            WHEN t.transaction_type IN (
                'REDEMPTION', 'SWITCH_OUT'
            ) THEN -t.amount_inr
            ELSE 0
        END) AS net_flows_inr
    FROM transactions t
    JOIN clients c ON c.client_id = t.client_id
    WHERE t.transaction_status = 'Successful'
    GROUP BY c.city
)
SELECT
    city,
    net_flows_inr,
    RANK() OVER (ORDER BY net_flows_inr DESC) AS city_rank
FROM city_flows
ORDER BY city_rank;


-- 6. Monthly transaction success and failure rates.
SELECT
    substr(transaction_date, 1, 7) AS month,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'Successful'
             THEN 1 ELSE 0 END) AS successful_transactions,
    SUM(CASE WHEN transaction_status = 'Failed'
             THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(
        100.0 * SUM(CASE WHEN transaction_status = 'Failed'
                         THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS failure_pct
FROM transactions
GROUP BY substr(transaction_date, 1, 7)
ORDER BY month;


-- 7. SIP registration value by status.
SELECT
    sip_status,
    COUNT(*) AS sip_count,
    SUM(monthly_amount) AS monthly_value_inr,
    ROUND(AVG(monthly_amount), 2) AS average_monthly_sip_inr
FROM sips
GROUP BY sip_status
ORDER BY monthly_value_inr DESC;


-- 8. Top 5 schemes by successful net investment flows.
WITH scheme_flows AS (
    SELECT
        s.scheme_id,
        s.scheme_name,
        s.category,
        SUM(CASE
            WHEN t.transaction_type IN (
                'PURCHASE', 'SIP_INSTALLMENT', 'SWITCH_IN'
            ) THEN t.amount_inr
            WHEN t.transaction_type IN (
                'REDEMPTION', 'SWITCH_OUT'
            ) THEN -t.amount_inr
            ELSE 0
        END) AS net_flows_inr
    FROM transactions t
    JOIN schemes s ON s.scheme_id = t.scheme_id
    WHERE t.transaction_status = 'Successful'
    GROUP BY s.scheme_id, s.scheme_name, s.category
)
SELECT
    scheme_name,
    category,
    net_flows_inr
FROM scheme_flows
ORDER BY net_flows_inr DESC
LIMIT 5;