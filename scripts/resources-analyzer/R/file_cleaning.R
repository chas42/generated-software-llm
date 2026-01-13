fileCleaning <- function(basePath, fileName) {
  
  fileLocation <- paste0(basePath, "/data/", fileName)
  
  # lendo o arquivo informado
  processesgpt2 <- readLines(fileLocation)
  # separando cada linha do arquivo por espaços em branco
  processesgpt2 <- gsub("\\s+", " ", processesgpt2)
  # o comando que gera os arquivos insere um cabeçalho para cada registro, 
  # então é necessárido detecatalo através das string 'USER' e retiralos do
  # comando exceto pelo primeiro
  processesgpt2 <- processesgpt2[-grep(pattern = "USER", processesgpt2)[-1]]
  
  # iteração por cada elemento para limpeza de cada linha
  for (i in 1:length(processesgpt2)) {
    # listando os elementos separados por espaco em um vetor
    vetor <- unlist(strsplit(processesgpt2[i], " "))
    # unindo os seis primeiros elementos que, pois nao sao separados por espaco
    string1 <- paste(vetor[1:6], collapse = ",")
    # o ultimo elemento representa o comando utilizado para inicializar o 
    # processo, entap é necessário uni-lo em apenas uma string, alem de manter 
    # os espacos contidos anteriormente
    string2 <- paste(",\"",paste(vetor[7:length(vetor)], collapse = " "),"\"", sep = "")
    # união das duas strings geradas
    processesgpt2[i] <- paste(string1,string2,sep="")
  }
  
  # ajustando o cabeacalho
  processesgpt2[1] <- "CURRENT_TIME,USER,PID,VSZ,RSS,MEM,COMMAND"
  # removendo a extensao .txt do arquivo
  fileName <- unlist(strsplit(fileName, ".txt"))
  # adicionando .csv como extensao do arquivo
  file_path <- paste0(basePath, "/data/", fileName, "_clean.csv")
  writeLines(processesgpt2, con = file_path)
}
