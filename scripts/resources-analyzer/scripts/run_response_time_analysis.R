run_response_time_analysis <- function(basePath,fileName, modelname) {
  
  print("Start generate response time graphs")
  fileLocation <- paste0(basePath,"/data/", fileName)

    df <- read.csv(file = fileLocation, header = TRUE, strip.white = TRUE, 
                 na.strings = "", sep = ",", stringsAsFactors = FALSE)
  
  time_interval <- 0.2
  
  # Filtra o data frame
  df <- df %>% 
    mutate(
      time = as.POSIXct(timeStamp / 1000, origin = "1970-01-01", tz = "UTC"),
      timeInHours = as.numeric(difftime(time, time[1], units = "hours")),
    ) %>%
    filter(timeInHours <= 50 ) %>%
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
  
  graph_name <- paste0(basePath, "/results/", "response_time_analysis_", modelname, ".png")
  ggsave(graph_name, plot = graph, width = 4, height = 3)
  
  print("End generate response time graphs")
  # statisc_tests(dados_media$grupo_tempo, dados_media$media_valor, "responseTime", modelName)
}