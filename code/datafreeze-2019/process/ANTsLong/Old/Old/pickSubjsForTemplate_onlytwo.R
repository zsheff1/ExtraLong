### This script finds subjects that span the necessary, age, sex, race and session
### spacing to build a group template with. This script only pulls from people
### who were assessed twice, so that their single subject template can be utilized
### directly.
###
### Ellyn Butler
### October 28, 2020

set.seed(20)

require(dplyr)

# Load data
demo_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/scanid_to_seslabel_demo_20200531.csv')
diag_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/diagnosis_long_final.csv')
qa_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/antssstExclude.csv')
param_df <- read.csv('~/Documents/ExtraLong/data/acquisitionInfo/parameters.csv')

qa_df <- qa_df[qa_df$antssstExclude == FALSE, ]
row.names(qa_df) <- 1:nrow(qa_df)

# Filter out subjects who are not in diag_df
demo_df <- demo_df[demo_df$bblid %in% diag_df$bblid & demo_df$num_timepoints == 2, ] # Down to 530 from 2341

# Filter out sessions with poor quality metrics
demo_df <- demo_df[demo_df$bblid %in% qa_df$bblid, ]

demo_df <- merge(demo_df, param_df)


# Compute variables
demo_df$white <- recode(demo_df$race, `1`='Yes', .default='No')
ageFirstSecond <- function(i) {
  bblid <- demo_df[i, 'bblid']
  age_first <- demo_df[demo_df$bblid == bblid & demo_df$timepoint == 1, 'scanage_years']
  age_second <- demo_df[demo_df$bblid == bblid & demo_df$timepoint == 2, 'scanage_years']
  if (length(age_second) > 0) { # Should always be the case
    c(age_first, age_second)
  } else { c(age_first, NA) }
}

demo_df[, c('age_first', 'age_second')] <- t(sapply(1:nrow(demo_df), ageFirstSecond))

demo_df$age_first_under16 <- ifelse(demo_df$age_first < 16, TRUE, FALSE)

# 32 scans for template: 2 people per category,
# sex(2)*white(2)*age_first_under12(2)*age_third_over18(2)
many_df <- demo_df[demo_df$timepoint == 2, ]
row.names(many_df) <- 1:nrow(many_df)

many_df$diff_age1to2 <- many_df$age_second - many_df$age_first
many_df$TrioTim <- ifelse(many_df$ManufacturersModelName == 'TrioTim', TRUE, FALSE)

bblid_df <- expand.grid(1:2, c('Yes', 'No'), c(TRUE, FALSE))
names(bblid_df) <- c('sex', 'white', 'age_first_under16')

selectbblid <- function(i) {
  sex <- bblid_df[i, 'sex']
  white <- bblid_df[i, 'white']
  age_first_under16 <- bblid_df[i, 'age_first_under16']
  trio_t2 <- bblid_df[i, 'age_first_under16']
  boo <- many_df[many_df$sex == sex & many_df$white == white
    & many_df$age_first_under16 == age_first_under16 & many_df$diff_age1to2 > 1 &
    many_df$TrioTim == trio_t2, ]
  if (nrow(boo) > 0) {
    bblids <- many_df[many_df$sex == sex & many_df$white == white
      & many_df$age_first_under16 == age_first_under16 & many_df$diff_age1to2 > 1 &
      many_df$TrioTim == trio_t2, 'bblid']
  } else {
    bblids <- many_df[many_df$sex == sex & many_df$white == white
      & many_df$age_first_under16 == age_first_under16 & many_df$diff_age1to2 > 1, 'bblid']
  }
  print(length(bblids))
  sample(bblids, 2, replace=FALSE)
}

bblid_df[, c('bblid1', 'bblid2')] <- t(sapply(1:nrow(bblid_df), selectbblid))


# Create dataframe of bblids and seslabels for bblids selected and their first
# through third sessions
template_df <- demo_df[demo_df$bblid %in% c(bblid_df$bblid1, bblid_df$bblid2) & demo_df$timepoint %in% 1:2, ]

# 18.75% of the template sample is Prismas, while 10.17% of the total sample are

# Sanity checks on balance
mean(template_df[template_df$sex == 1, 'age_first'])
mean(template_df[template_df$sex == 2, 'age_first'])
mean(template_df[template_df$white == 'Yes', 'age_first'])
mean(template_df[template_df$white == 'No', 'age_first'])

mean(template_df[template_df$sex == 1, 'age_second'])
mean(template_df[template_df$sex == 2, 'age_second'])
mean(template_df[template_df$white == 'Yes', 'age_second'])
mean(template_df[template_df$white == 'No', 'age_second'])



write.csv(template_df[, c('bblid', 'seslabel')], '~/Documents/ExtraLong/data/groupTemplates/subjsFromN752_set1.csv', row.names=FALSE)









#
