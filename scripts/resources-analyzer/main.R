# ============================
# Dependências do projeto
# ============================
install.packages("trend")
install.packages("knitr")
install.packages("dplyr")
install.packages("ggplot2")
install.packages("gridExtra")
install.packages("Kendall")
install.packages("data.table")
install.packages("DBI")
install.packages("duckdb")


library(DBI)
library(duckdb)
library(trend)
library(knitr)
library(dplyr)
library(ggplot2)
library(gridExtra)
library(Kendall)
library(data.table)
# ============================
# Carregar funções
# ============================
lapply(list.files("R", full.names = TRUE), source)
lapply(list.files("scripts", full.names = TRUE), source)

# configs
source("config/paths.R")

run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-python-fast-api.csv"),
  modelName = "python-fast-api-monitor",
  title = "python fast api monitor"
)
fileCleaning(
  basePath = paths$base,
  fileName = "processes-monitor-python-fast-api.txt"
)
run_processes_analysis(
  basePath = paths$base,
  fileName = "processes-monitor-python-fast-api-clean.csv",
  modelName = "python-fast-api-monitor",
  commandString = "python code/app.py"
)

# ============================
# Executar scripts
# ============================

run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-credit-card-python.csv"),
  modelName = "python-credit-card",
  title = "Credit Card Python"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-image-converter-python.csv"),
  modelName = "python-image-converter",
  title = "Convert Image Python"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-monitor-python.csv"),
  modelName = "python-monitor",
  title = "Monitorpython"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-uptime-python.csv"),
  modelName = "python-uptime",
  title = "Uptime Python"
)
# ============================
# Executar scripts
# ============================

run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-credit-card-rust.csv"),
  modelName = "rust-credit-card",
  title = "Credit Card rust"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-image-converter-rust.csv"),
  modelName = "rust-image-converter",
  title = "Convert Image rust"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-monitor-rust.csv"),
  modelName = "rust-monitor",
  title = "Monitor  rust"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-uptime-rust.csv"),
  modelName = "rust-uptime",
  title = "Uptime JS"
)

# ============================
# Executar scripts
# ============================

run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-credit-card-js.csv"),
  modelName = "js-credit-card",
  title = "Credit Card js"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-image-converter-js.csv"),
  modelName = "js-image-converter",
  title = "Convert Image js"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-monitor-js.csv"),
  modelName = "js-monitor",
  title = "Monitor  js"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-uptime-js.csv"),
  modelName = "js-uptime",
  title = "Uptime JS"
)


# imageConverterProcessesList <- c(
#   "processes-image-converter-python.txt",
#   "processes-monitor-python.txt",
#   "processes-credit-card-python.txt",
#   "processes-uptime-python.txt"
# )
# 
# for (imcp in imageConverterProcessesList) {
#   fileCleaning(
#     basePath = paths$base,
#     fileName = imcp
#   )
# }

imcpCleanList <- list(
  c("processes-image-converter-python_clean.csv",
    "python-image-converter",
    "python3 app.py") ,
  c("processes-monitor-python_clean.csv",
    "python-monitor",
    "python3 code_prompt1.py") ,
  c("processes-credit-card-python_clean.csv",
    "python-credit-card",
    "python3 COD_CREDIT_CARD1.py") ,
  c("processes-uptime-python_clean.csv",
    "python-uptime",
    "python3 code_prompt1.py") 
)

for (imcpClean in imcpCleanList) {
  
  print(paste0("START ", imcpClean[2]))
  run_processes_analysis(
    basePath = paths$base,
    fileName = imcpClean[1],
    modelName = imcpClean[2],
    commandString = imcpClean[3]
  )
  print(paste0("END ", imcpClean[2]))
}


rtimcList <- list(
  c("response-time-image-converter-python.csv",
    "python-image-converter") ,
  c("response-time-monitor-python.csv",
    "python-monitor") ,
  c("response-time-uptime-python.csv",
    "python-uptime")
  # c("response-time-credit-card-python.csv",
  #   "python-credit-card")
)

for (rtimc in rtimcList) {
  run_response_time_analysis(
    basePath = paths$base,
    fileName = rtimc[1],
    modelName = rtimc[2]
  )
}


run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-js-image-converter.csv"),
  modelName = "js-image-converter",
  title = "Convert Image JS"
)



run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-rust-convert-image.csv"),
  modelName = "rust-image-converter",
  title = "Convert Image RUST"
)

imageConverterProcessesList <- c(
  "processes-image-converter-js.txt",
  "processes-image-converter-python.txt",
  "processes-image-converter-rust.txt"
)

for (imcp in imageConverterProcessesList) {
  fileCleaning(
    basePath = paths$base,
    fileName = imcp
  )
}


imcpCleanList <- list(
  # c("processes-image-converter-js_clean.csv",
  #   "image-converter-js",
  #   "npm start"),
  c("processes-image-converter-python_clean.csv",
    "image-converter-python",
    "python3 app.py") #,
  # c("processes-image-converter-rust_clean.csv",
  #   "image-converter-rust",
  #   "/home/cesar/gif_converter/target/debug/gif_converter")
)

for (imcpClean in imcpCleanList) {
  
  print(paste0("START ", imcpClean[2]))
  run_processes_analysis(
    basePath = paths$base,
    fileName = imcpClean[1],
    modelName = imcpClean[2],
    commandString = imcpClean[3]
  )
  print(paste0("END ", imcpClean[2]))
}


creditCardProcessesList <- c(
  "processes-credit-card-js.txt",
  "processes-credit-card-python.txt",
  "processes-credit-card-rust.txt"
)

for (crcp in creditCardProcessesList) {
  fileCleaning(
    basePath = paths$base,
    fileName = crcp
  )
}

crcpCleanList <- list(
  c("processes-credit-card-js_clean.csv",
    "credit-card-js",
    "npm start"),
  c("processes-credit-card-python_clean.csv",
    "credit-card-python",
    "python3 COD_CREDIT_CARD1.py"),
  c("processes-credit-card-rust_clean.csv",
    "credit-card-rust",
    "/home/cesar/Downloads/Credit_Card/target/debug/creditcardservice")
)

for (crcpClean in crcpCleanList) {
  
  print(paste0("START ", crcpClean[2]))
  run_processes_analysis(
    basePath = paths$base,
    fileName = crcpClean[1],
    modelName = crcpClean[2],
    commandString = crcpClean[3]
  )
  print(paste0("END ", crcpClean[2]))
}



c(
  "data/processes-credit-card-js.txt",
  "data/processes-credit-card-python.txt",
  "data/processes-js-image-converter.txt",
  "data/processes-python-image-converter.txt",
  "data/processes-rust-convert-image.txt",
  "data/processes-rust-credit-card.txt"
)




run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-credit-card-js.csv"),
  modelName = "js-credit-card",
  title = "Credit Card JS"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-credit-card-python.csv"),
  modelName = "python-credit-card",
  title = "Credit Card PYTHON"
)
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-rust-credit-card.csv"),
  modelName = "rust-credit-card",
  title = "Credit Card RUST"
)

rtimcList <- c(
  "response-time-image-converter-js.csv",
  "response-time-image-converter-python.csv",
  "response-time-image-converter-rust.csv"
)

for (rtimc in rtimcList) {
  modelName <- sub("^response-time-|\\.csv$", "", rtimc)
  run_response_time_analysis(
    basePath = paths$base,
    fileName = rtimc,
    modelname = modelName
  )
}

