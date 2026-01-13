confidence_interval_slope <- function(x, y) {
  modelo <- lm(y ~ x)
  cor_xy <- cor(x, y)
  n <- length(x)
  t <- qt(0.975, df = n - 2)
  
  slope <- coef(modelo)[2]
  erro <- (sd(y) / sd(x)) * sqrt((1 - cor_xy^2) / (n - 2))
  
  slope + c(-1, 1) * t * erro
}

statisc_tests <- function(x, y, testName, modelName) {
  
  mk <- Kendall::MannKendall(y)
  slope <- coef(lm(y ~ x))[2]
  ic <- confidence_interval_slope(x, y)
  
  df <- data.frame(
    TEST = testName,
    MODEL = modelName,
    P_VALUE = mk$sl,
    SLOPE = slope,
    CONFIDENCE = paste(ic[1], ic[2]),
    MEAN = mean(y)
  )
  
  write.table(
    df,
    file = paste0("~/Documents/dados_", testName, ".csv"),
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