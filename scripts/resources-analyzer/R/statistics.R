confidence_interval_slope <- function(x, y) {
  modelo <- lm(y ~ x)
  confint(modelo)[2, ]
}

statisc_tests <- function(x, y, testName, modelName) {
  
  if(length(x) < 3){
    stop("É necessário pelo menos 3 pontos para análise.")
  }
  
  mk <- Kendall::MannKendall(y)
  slope <- coef(lm(y ~ x))[2]
  ic <- confidence_interval_slope(x, y)
  
  df <- data.frame(
    TEST = testName,
    MODEL = modelName,
    P_VALUE = mk$sl,
    SLOPE = slope,
    CI_LOW = ic[1],
    CI_HIGH = ic[2],
    MEAN = mean(y)
  )
  
  write.table(
    df,
    file = paste0(paths$base,"results/",modelName,"/","statistic-test.csv"),
    append = TRUE,
    sep = ",",
    col.names = FALSE,
    row.names = FALSE
  )
}

growth_Rate <- function(vetor){
  start <- head(vetor, n = 1)
  end <- tail(vetor, n = 1)
  tax <- ((end - start) / start) *100
  return(tax)
}