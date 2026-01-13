# ============================
# Dependências do projeto
# ============================
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

# ============================
# Executar scripts
# ============================
run_resource_analysis(
  pathFile = paste0(paths$base,"data/monitoring-gpt-gustavo_10th-0.1s.csv"),
  modelName = "convert-image-gpt",
  title = "Convert Image App GPT"
)

# fileCleaning(
#   basePath = paths$base,
#   fileName = "processes-gpt-gustavo_10th-0.1s.txt"
# )

run_processes_analysis(
  basePath = paths$base,
  fileName = "processes-gpt-gustavo_10th-0.1s_clean.csv",
  modelName = "convert-image-gpt",
  commandString = "python3 app.py"
)

run_response_time_analysis(basePath = paths$base,
                           fileName = "response-time-image-converter.csv",
                           modelname = "convert-image-gpt")


