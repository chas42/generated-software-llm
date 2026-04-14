
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
    filter(timeInHours <= 52 )
  
  metrics_df <- data.frame(
  metric = c(
    "totalCpuUsage", 
    "totalMemory",
    "availableMemory",
    "usedMemory", 
    "percentageMemory", 
    "buffersMemory",
    "cachedMemory", 
    "totalSwap",
    "freeSwap",
    "usedSwap", 
    "percentageSwap", 
    "totalPartition",
    "usedPartition",
    "freePartition",
    "percentagePartition", 
    "total_IO_read", 
    "total_IO_write",
    "readOps",
    "writeOps",
    "readLatency",
    "writeLatency",
    "readBytesPerSec",
    "writeBytesPerSec",
    "procCpu",
    "procMemory",
    "procThreads",
    "GC_gen0",
    "GC_gen1",
    "GC_gen2"
  ),
  unit = c(
    "%",       # totalCpuUsage
    "GB",      # totalMemory
    "GB",      # availableMemory
    "GB",      # usedMemory
    "%",       # percentageMemory
    "GB",      # buffersMemory
    "GB",      # cachedMemory
    "GB",      # totalSwap
    "GB",      # freeSwap
    "GB",      # usedSwap
    "%",       # percentageSwap
    "GB",      # totalPartition
    "GB",      # usedPartition
    "GB",      # freePartition
    "%",       # percentagePartition
    "GB",      # total_IO_read
    "GB",      # total_IO_write
    "ops",     # readOps
    "ops",     # writeOps
    "ms",      # readLatency
    "ms",      # writeLatency
    "B/s",     # readBytesPerSec
    "B/s",     # writeBytesPerSec
    "%",       # procCpu
    "bytes",   # procMemory
    "count",   # procThreads
    "count",   # GC_gen0
    "count",   # GC_gen1
    "count"    # GC_gen2
  ),
  legend = c(
    "Total CPU Usage", 
    "Total Memory",
    "Available Memory",
    "Used Memory", 
    "Memory Usage", 
    "Buffers Memory",
    "Cached Memory", 
    "Total Swap",
    "Free Swap",
    "Used Swap", 
    "Swap Usage", 
    "Total Partition",
    "Used Partition",
    "Free Partition",
    "Partition Usage", 
    "Total IO Read", 
    "Total IO Write",
    "Read Operations",
    "Write Operations",
    "Read Latency",
    "Write Latency",
    "Read Bytes/sec",
    "Write Bytes/sec",
    "Process CPU",
    "Process Memory",
    "Process Threads",
    "GC Generation 0",
    "GC Generation 1",
    "GC Generation 2"
  ),
  stringsAsFactors = FALSE
)
  
  for (i in seq_len(nrow(metrics_df))) {
    metric <- metrics_df$metric[i]
    unit <- metrics_df$unit[i]
    legend <- metrics_df$legend[i]
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
      graphTitle = paste(metric, title,sep = " "),
      df = dataFrameToPrint,
      xLegend = "Time (hour)",
      yLegend = paste(legend, "(", unit, ")")
      # yStart = yStart,
      # yEnd = yEnd,
      # yBy = yBy
    )
    
    graph_name <- paste0(paths$base, "results/",modelName,"/",metric, "_", "analysis", "_", modelName, 
                         ".png")
    ggsave(graph_name, plot = graph, width = 4, height = 3)
    
    statisc_tests(df$timeInHours,df[[metric]],paste0(modelName,"-resource-",metric),modelName)
    
  }
  
  print(paste0("run resource analysis complete",modelName))
  
}
