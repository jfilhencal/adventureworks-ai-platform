-- AdventureWorksDW sample query for monthly sales trend
-- TODO: Join with DimDate for calendar grouping and filters.
SELECT
    CONVERT(VARCHAR(7), OrderDate, 120) AS month_key,
    SUM(SalesAmount) AS revenue,
    COUNT_BIG(*) AS order_count
FROM FactInternetSales
GROUP BY CONVERT(VARCHAR(7), OrderDate, 120)
ORDER BY month_key;
