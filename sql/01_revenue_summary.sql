-- AdventureWorksDW sample query for revenue summary
-- TODO: Replace with production warehouse views and date dimensions.
SELECT
    SUM(SalesAmount) AS total_revenue,
    COUNT_BIG(*) AS order_count
FROM FactInternetSales;
