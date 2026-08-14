run_response_time_analysis <- function(basePath, fileName, modelName) {
  
  print(paste0("Start generate response time graphs of ", modelName))
  
  fileLocation <- file.path(basePath, "data", fileName)
  
  con <- dbConnect(duckdb::duckdb())
  
  time_interval <- 0.2
  
  query <- paste0("
    WITH base AS (
      SELECT 
        timeStamp / 1000.0 AS time_sec,
        elapsed
      FROM read_csv_auto('", fileLocation, "')
    ),
    normalized AS (
      SELECT 
        (time_sec - MIN(time_sec) OVER()) / 3600.0 AS timeInHours,
        elapsed
      FROM base
    )
    SELECT 
      FLOOR(timeInHours / ", time_interval, ") * ", time_interval, " AS time,
      AVG(elapsed) AS value
    FROM normalized
    WHERE timeInHours < 50
    GROUP BY time
    ORDER BY time
  ")
  
  df <- dbGetQuery(con, query)
  
  dbDisconnect(con, shutdown = TRUE)
  
  # Geração do gráfico
  graph <- generate_graph(
    graphTitle,
    df = df,
    xLegend = "Time (hours)",
    yLegend = "Response Time (ms)"
  )
  
  graph_name <- file.path(basePath, "results", modelName, "response-time-analysis.png")
  
  ggsave(graph_name, plot = graph, width = 4, height = 3)
  
  statisc_tests(df$time, df$value, "response-time", modelName)
  
  print("End generate response time graphs")
}
