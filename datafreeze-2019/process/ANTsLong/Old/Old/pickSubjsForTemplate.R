### This script finds subjects that span the necessary, age, sex, race and session
### spacing to build a group template with.
###
### Ellyn Butler
### September 28, 2020

set.seed(20)

require(dplyr)

# Load data
demo_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/scanid_to_seslabel_demo_20200531.csv')
diag_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/diagnosis_long_final.csv')

# Filter out subjects who are not in diag_df
demo_df <- demo_df[demo_df$bblid %in% diag_df$bblid, ] # Down to 1840 from 2341
row.names(demo_df) <- 1:nrow(demo_df)

# LATER: Filter out sessions with poor quality metrics


# Compute variables
demo_df$white <- recode(demo_df$race, `1`='Yes', .default='No')
ageFirstThird <- function(i) {
  bblid <- demo_df[i, 'bblid']
  age_first <- demo_df[demo_df$bblid == bblid & demo_df$timepoint == 1, 'scanage_years']
  age_third <- demo_df[demo_df$bblid == bblid & demo_df$timepoint == 3, 'scanage_years']
  if (length(age_third) > 0) {
    c(age_first, age_third)
  } else { c(age_first, NA) }
}

demo_df[, c('age_first', 'age_third')] <- t(sapply(1:nrow(demo_df), ageFirstThird))
#demo_df$age_first_under16 <- sapply(1:nrow(demo_df), function(x)
#  {ifelse(demo_df[x, 'age_first'] <= 16, 'Yes', 'No')})
#demo_df$age_third_over18 <- sapply(1:nrow(demo_df), function(i)
#  {ifelse(demo_df[i, 'age_third'] >= 18, 'Yes', 'No')})

# 32 scans for template: 2 people per category,
# sex(2)*white(2)*age_first_under12(2)*age_third_over18(2)
many_df <- demo_df[demo_df$num_timepoints > 2 & demo_df$timepoint == 1, ]
row.names(many_df) <- 1:nrow(many_df)

many_df$diff_age1to3 <- many_df$age_third - many_df$age_first

scanid_df <- expand.grid(1:2, c('Yes', 'No'), c('Yes', 'No'))
names(scanid_df) <- c('sex', 'white', 'age_first_under16')

selectbblid <- function(i) {
  sex <- scanid_df[i, 'sex']
  white <- scanid_df[i, 'white']
  age_first_under16 <- scanid_df[i, 'age_first_under16']
  bblids <- many_df[many_df$sex == sex & many_df$white == white
    & many_df$age_first_under16 == age_first_under16 & many_df$diff_age1to3 > 2, 'bblid']
  sample(bblids, 2, replace=FALSE)
}

scanid_df[, c('bblid1', 'bblid2')] <- t(sapply(1:nrow(scanid_df), selectbblid))

bblids <- c(scanid_df$bblid1, scanid_df$bblid2)


# Create dataframe of bblids and seslabels for bblids selected and their first
# through third sessions
template_df <- demo_df[demo_df$bblid %in% bblids & demo_df$timepoint %in% 1:3, ]

# Sanity checks on balance
mean(template_df[template_df$sex == 1, 'age_first'])
mean(template_df[template_df$sex == 2, 'age_first'])
mean(template_df[template_df$white == 'Yes', 'age_first'])
mean(template_df[template_df$white == 'No', 'age_first'])

mean(template_df[template_df$sex == 1, 'age_third'])
mean(template_df[template_df$sex == 2, 'age_third'])
mean(template_df[template_df$white == 'Yes', 'age_third'])
mean(template_df[template_df$white == 'No', 'age_third'])













#
