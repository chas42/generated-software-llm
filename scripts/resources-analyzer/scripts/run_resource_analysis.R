
run_resource_analysis <- function(pathFile, modelName, title) {
  
  df <- read.csv(
    file = pathFile, 
    header = T, 
    strip.white = T, 
    na.strings = "", 
    sep=",")
  
  df <- df %>% 
    mutate(currentTime = as.POSIXct(df$currentTime, format = "%Y-%m-%d %H:%M:%OS")) %>%
    mutate(currentTime = difftime(df$currentTime, df$currentTime[1], units = "hours")) %>%
    mutate(timeInHours = as.numeric(currentTime, units = "hours")) %>%
    mutate(usedMemory = usedMemory / 10^9, 
           usedSwap = usedSwap / 10^9, 
           cachedMemory = cachedMemory / 10^9, 
           buffersMemory = buffersMemory / 10^9, 
           totalMemory = totalMemory / 10^9, 
           availableMemory = availableMemory / 10^9, 
           totalSwap = totalSwap / 10^9, 
           freeSwap = freeSwap / 10^9, 
           totalPartition = totalPartition / 10^9, 
           usedPartition = usedPartition / 10^9, 
           freePartition = freePartition / 10^9,
           total_IO_read = total_IO_read / 10^9,
           total_IO_write = total_IO_write / 10^9) %>%
    filter(timeInHours <= 50 )
  
  metrics_df <- data.frame(
    metric = c(
      "totalCpuUsage", 
      "usedMemory", 
      "percentageMemory", 
      "buffersMemory",
      "cachedMemory", 
      "usedSwap", 
      "percentageSwap", 
      "usedPartition",
      "percentagePartition", 
      "total_IO_read", 
      "total_IO_write"
    ),
    unit    = c(  "%",  "GB", "%",  "GB", "GB", "GB", "%",  "GB", "%",  "GB", "GB"),
    # ystart  = c(  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0),
    # yend    = c(  100,  5.0,  100,  1.0,  5.0,  1,    100,  100,  100,  10,   1600),
    # yby     = c(  10,   0.5,  10,   0.1,  0.5,  0.1,  10,   10,   10,   1,    400),
    stringsAsFactors = FALSE
  )
  
  for (i in seq_len(nrow(metrics_df))) {
    metric <- metrics_df$metric[i]
    unit <- metrics_df$unit[i]
    # yStart <- metrics_df$ystart[i]
    # yEnd <- metrics_df$yend[i]
    # yBy <-metrics_df$yby[i]
    
    if (!(metric %in% colnames(df))) {
      warning(paste("Métrica", metric, "não encontrada no dataset. Pulando..."))
      next
    }
    
    if (all(is.na(df[[metric]]))) {
      warning(paste("Métrica", metric, "está vazia. Pulando..."))
      next
    }
    
    dataFrameToPrint <- data.frame(
      time = df$timeInHours,
      value = df[[metric]]
    )
    
    graph <- generate_graph(
      graphTitle = paste(metric, modelNameToGraphTitle,sep = " "),
      df = dataFrameToPrint,
      xLegend = "Time (hour)",
      yLegend = paste(metric, "(", unit, ")"),
      # yStart = yStart,
      # yEnd = yEnd,
      # yBy = yBy
    )
    
    graph_name <- paste0(paths$base, "results/",metric, "_", "analysis", "_", modelName, 
                         ".png")
    ggsave(graph_name, plot = graph, width = 4, height = 3)
    
  }
  
}
