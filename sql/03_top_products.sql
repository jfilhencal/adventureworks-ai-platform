-- AdventureWorksDW sample query for top products
-- TODO: Add product categories, ranking, and time filters.
SELECT TOP 10
    p.EnglishProductName AS product_name,
    SUM(f.SalesAmount) AS revenue
FROM FactInternetSales AS f
JOIN DimProduct AS p ON f.ProductKey = p.ProductKey
GROUP BY p.EnglishProductName
ORDER BY revenue DESC;
