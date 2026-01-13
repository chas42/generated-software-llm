generate_graph <- function(df, graphTitle, xLegend, yLegend,yStart,yEnd,yBy) {
  time_interval <- 1.0
  
  dados_media <- df %>%
    mutate(grupo_tempo = ((time - min(time)) %/% time_interval) * time_interval) %>%
    group_by(grupo_tempo) %>%
    summarise(media_valor = mean(value, na.rm = TRUE))
  
  graph <- ggplot(dados_media, aes(x = grupo_tempo, y = media_valor)) +
    # graph <- ggplot(df, aes(x = time, y = value)) +
    geom_line(color = "blue") +
    # geom_point(size =3 , color = "red")
    # labs(x = xLegend, y = yLegend) +
    labs( x = xLegend, y = yLegend) +
    # scale_x_continuous(breaks = seq(0, 50, by = 5)) +
    # scale_y_continuous(breaks = seq(yStart, yEnd, by = yBy)) +
    # coord_cartesian(xlim = c(0, 50)) +
    # coord_cartesian(ylim = c(yStart, yEnd)) +
    scale_x_continuous(breaks = seq(0, 48, by = 12)) +
    coord_cartesian(xlim = c(0, 48)) +
    theme_light() +
    theme(
      axis.text.x = element_text(size = 12),
      axis.text.y = element_text(size = 12),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      panel.background = element_blank(),
      plot.background = element_rect(fill = "white", color = NA)
    )
  
  return(graph)
}
