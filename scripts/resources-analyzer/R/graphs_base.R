generate_graph <- function(df, graphTitle, xLegend, yLegend 
                           # ,yStart, yEnd, yBy
                           ) {
  
  time_interval <- 0.5
  
  dados_media <- df %>%
    mutate(grupo_tempo = ((time - min(time)) %/% time_interval) * time_interval) %>%
    group_by(grupo_tempo) %>%
    summarise(media_valor = mean(value, na.rm = TRUE))
  
  graph <- ggplot(dados_media, aes(x = grupo_tempo, y = media_valor)) +
    
    geom_line(color = "#9CDBE8", size = 0.9) +        # linha mais grossa
    # geom_point(color = "#1A4FA3", size = 2) +         # pontos nos dados
    
    labs(
      # title = graphTitle,
      x = xLegend,
      y = yLegend
    ) +
    
    scale_x_continuous(
      breaks = seq(0, 48, by = 8)
    ) +
    
    # scale_y_continuous(
    #   breaks = seq(yStart, yEnd, by = yBy)
    # ) +
    
    coord_cartesian(
      xlim = c(0, 48),
      # ylim = c(yStart, yEnd)
    ) +
    
    theme_minimal(base_size = 14) +
    
    theme(
      # plot.title = element_text(
      #   size = 18,
      #   face = "bold",
      #   hjust = 0.5
      # ),
      
      axis.title = element_text(size = 14),
      
      axis.text = element_text(size = 12),
      
      panel.grid.major = element_line(
        color = "gray85",
        size = 0.3
      ),
      
      panel.grid.minor = element_blank()
    )
  
  return(graph)
}