library(dplyr)
setwd("C://Users//me//Documents//CNEconCoerc")
#setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
#um... the above line doesn't work when executing as R code in Power BI
#because it's not rstudio api, and anyway since the way power BI runs R scripts is you copy-paste them (lol) there will be no source directory
#raw <- read.csv("prod_country_trade_combined.csv")
raw <- read.csv("2023//prod_trade_combined_2023.csv")
#? something weird happened with duplicates at some point with the critical minerals
#but it's fixed now...
countries.raw <- read.csv("countries.csv")
g7aus <- countries.raw$country[which(countries.raw$isg7aus == 1)]
partners <- countries.raw$country[which(countries.raw$isPartner == 1)]
all.countries <- unique(raw$country)

#um... need to go thru each product+year and if the sum of trade_percent for that product+year isn't 100%,
#then add an "other" to make the trade_percent sum to 100% so grand total (GT) trade value % is correct

#but after removing countries that are < total threshold bc they make the data more unnecessarily granular
keep_countries <- raw %>% group_by(country) %>% summarize(total_val = sum(trade_value)) %>% filter(total_val > 2000000)
raw <- raw %>% subset(country %in% keep_countries$country)

remaining.df <- raw %>% group_by(productcode, year) %>% summarize(tr_pct_sum = sum(trade_percent), tr_val_sum = sum(trade_value)) %>% subset(tr_pct_sum < .99) %>%
  mutate(remaining_val = (tr_val_sum/tr_pct_sum)*(1-tr_pct_sum), remaining_pct = 1-tr_pct_sum) %>%
  select(productcode, year, remaining_val, remaining_pct) %>% rename(trade_value = remaining_val, trade_percent = remaining_pct) %>% mutate(country = "Other")

#and then rbind to raw and stuff

g7.df <- raw %>% subset(country %in% g7aus) %>% group_by(productcode, year) %>% summarize(trade_value = sum(trade_value), trade_percent = sum(trade_percent))
partner.df <- raw %>% subset(country %in% partners) %>% group_by(productcode, year) %>% summarize(trade_value = sum(trade_value), trade_percent = sum(trade_percent))
g7.df$country = "G7 + Aus"
partner.df$country = "Partner countries"
main <- bind_rows(raw, g7.df, partner.df, remaining.df)

countries <- data.frame(country = all.countries) %>% mutate(isg7aus = ifelse(country %in% g7aus, 1, 0), isPartner = ifelse(country %in% partners, 1, 0))
#outputs two tables "countries" and "main"
rm(raw, g7aus, partners, countries.raw, g7.df, partner.df, remaining.df, keep_countries, all.countries)