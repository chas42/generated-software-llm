run_throughput_analysis <- function(basePath, fileName, modelName) {
  
  print(paste0("Start generate throughput graph of ", modelName))
  
  fileLocation <- file.path(basePath, "data", fileName)
  
  con <- dbConnect(duckdb::duckdb())
  
  time_interval <- 0.2
  
  query_throughput <- paste0("
    WITH base AS (
      SELECT 
        timeStamp / 1000.0 AS time_sec
      FROM read_csv_auto('", fileLocation, "')
    ),
    normalized AS (
      SELECT 
        (time_sec - MIN(time_sec) OVER()) / 3600.0 AS timeInHours
      FROM base
    )
    SELECT 
      FLOOR(timeInHours / ", time_interval, ") * ", time_interval, " AS time,
      COUNT(*) / (", time_interval, " * 3600) AS value
    FROM normalized
    WHERE timeInHours < 50
    GROUP BY time
    ORDER BY time
  ")
  
  
  df <- dbGetQuery(con, query_throughput)
  
  dbDisconnect(con, shutdown = TRUE)
  
  # Geração do gráfico
  graph <- generate_graph(
    paste0("Throughput - ", modelName),
    df = df,
    xLegend = "Time (hours)",
    yLegend = "Throughput (req/s)"
  )
  
  graph_name <- file.path(basePath, "results", modelName, "throughput-analysis.png")
  
  ggsave(graph_name, plot = graph, width = 4, height = 3)
  
  statisc_tests(df$time, df$value, "Throughput", modelName)
  
  print("End generate Throughput graph")
}