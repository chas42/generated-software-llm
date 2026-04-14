run_processes_analysis <- function (basePath, fileName, modelName, commandString) {
  
  fileLocation <- paste0(basePath, "/data/", fileName)
  #leitura do arquivo criado apos a limpeza
  df <- read.csv(file = fileLocation,header = T,strip.white = T,na.strings = "",sep=",")
  # filtrando os processos com memoria maior que 0
  dados_filtrados <- df %>% filter(MEM>0)
  dados_filtrados$COMMAND <- as.factor(dados_filtrados$COMMAND)
  dados_filtrados$CURRENT_TIME <- as.POSIXct(dados_filtrados$CURRENT_TIME, format = "%d/%m/%Y+%H:%M:%S")
  proccessMEM <- dados_filtrados %>% filter( COMMAND == commandString)
  proccessMEM$CURRENT_TIME <- difftime(proccessMEM$CURRENT_TIME, proccessMEM$CURRENT_TIME[1], units = "hours") 
  proccessMEM <- proccessMEM %>% 
    mutate(timeInHours = as.numeric(CURRENT_TIME, units = "hours")) %>% 
    filter(timeInHours <= 48 )
  
  mktestProccess <- mk.test(proccessMEM$RSS)
  
  dataFrameToPrint <- data.frame(
    time = proccessMEM$timeInHours,
    value = kb_to_gb(proccessMEM$RSS)
  )
  
  statisc_tests(dataFrameToPrint$time, dataFrameToPrint$value, "proccess", modelName)
  
  process_graph <- generate_graph(
    df = dataFrameToPrint,
    graphTitle = "Proccess analysis",
    xLegend ="Time (hour)", 
    yLegend = "Used Memory (GB)"
    # yStart = yStartProcess,
    # yEnd = yEndProcess,
    # yBy = 0.1
  )
  graph_name <- paste(basePath,"/results/",modelName,"/","process-memory-analysis.png",sep = "")
  ggsave(graph_name,plot = process_graph, width = 4, height = 3)
  
  #############################################################################
  dados_filtrados$CURRENT_TIME <- difftime(
    dados_filtrados$CURRENT_TIME, 
    dados_filtrados$CURRENT_TIME[1], 
    units = "hours")
  
  dados_filtrados <- dados_filtrados %>% 
    filter(CURRENT_TIME <= 48 ) %>% 
    arrange(COMMAND, CURRENT_TIME)
  
  GROWTH_RATE <- dados_filtrados %>% 
    group_by(COMMAND) %>% 
    summarise(GROWTH_RATE = growth_Rate(RSS)) %>% 
    arrange(desc(GROWTH_RATE)) %>% 
    ungroup() %>% 
    slice_head(n = 5)
  
  write.csv(GROWTH_RATE, file = paste(basePath,"/results/",modelName,"/","process-growth_rate.csv",sep = ""),row.names = FALSE)
}