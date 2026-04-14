run_response_time_analysis <- function(basePath,fileName, modelName) {
  
  print(paste0("Start generate response time graphs of ",modelName))
  fileLocation <- paste0(basePath,"data/", fileName)

    df <- read.csv(file = fileLocation, header = TRUE, strip.white = TRUE, 
                 na.strings = "", sep = ",", stringsAsFactors = FALSE)
  
  time_interval <- 0.2
  
  # Filtra o data frame
  df <- df %>% 
    mutate(
      time = as.POSIXct(timeStamp / 1000, origin = "1970-01-01", tz = "UTC"),
      timeInHours = as.numeric(difftime(time, time[1], units = "hours")),
    ) %>%
    filter(timeInHours <= 48 ) %>%
    mutate(grupo_tempo = ((timeInHours - min(timeInHours)) %/% time_interval) * time_interval) %>%
    group_by(grupo_tempo) %>%
    summarise(media_valor = mean(elapsed, na.rm = TRUE)) %>%
    select(grupo_tempo,media_valor) 
  
  df <- data.frame(
    time = df$grupo_tempo,
    value = df$media_valor
  )
  
  graph <- generate_graph(
    graphTitle,
    df = df,
    xLegend = "Time (hours)",
    yLegend = "Response Time (ms)"
  )
  
  graph_name <- paste0(basePath, "/results/", modelName,"/","response-time-analysis.png")
  ggsave(graph_name, plot = graph, width = 4, height = 3)
  
  
  statisc_tests(df$time, df$value, "response-time", modelName)
  
  print("End generate response time graphs")
}